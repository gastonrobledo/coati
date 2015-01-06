

__author__ = 'gastonrobledo'
import json
from datetime import timedelta, datetime

from dateutil import parser
from flask import jsonify, request

from app.schemas import (Sprint, Project, SprintTicketOrder,
                         Column, TicketColumnTransition)
from app.redis import RedisClient
from app.api.resources.auth_resource import AuthResource


class SprintOrder(AuthResource):
    def __init__(self):
        super(SprintOrder, self).__init__()

    def post(self, project_pk, *args, **kwargs):
        data = request.get_json(force=True, silent=True)
        if data:
            for index, s in enumerate(data):
                sprint = Sprint.objects.get(pk=s)
                sprint.order = index
                sprint.save()
            # # add to redis
            r = RedisClient(channel=project_pk)
            r.store('order_sprints', **kwargs)
            return jsonify({'success': True}), 200
        return jsonify({"error": 'Bad Request'}), 400


class SprintList(AuthResource):
    def __init__(self):
        super(SprintList, self).__init__()

    def get(self, project_pk, *args, **kwargs):
        return Sprint.objects(project=project_pk, finalized=False).order_by(
            'order').to_json()

    def post(self, project_pk, *args, **kwargs):
        """
        Create Sprint
        """
        try:
            project = Project.objects.get(id=project_pk)
        except Project.DoesNotExist, e:
            return jsonify({"error": 'project does not exist'}), 400
        total = Sprint.objects(project=project_pk).count()
        sp = Sprint(project=project.to_dbref())
        sp.name = 'Sprint %d' % (total + 1)
        sp.save()
        # # add to redis
        r = RedisClient(channel=project_pk)
        r.store('new_sprint', **kwargs)
        return sp.to_json(), 201


class SprintInstance(AuthResource):
    def __init__(self):
        super(SprintInstance, self).__init__()

    def get(self, sp_id, *args, **kwargs):
        sp = Sprint.objects.get(pk=sp_id)
        return sp.to_json, 200

    def put(self, sp_id, *args, **kwargs):
        data = request.get_json(force=True, silent=True)
        if data:
            sp = Sprint.objects.get(pk=sp_id)
            sp.name = data.get('name', sp.name)
            if data.get('for_starting'):

                # sum all the ticket for the initial planning value
                sto = SprintTicketOrder.objects(sprint=sp, active=True)
                total_planned_points = 0
                for s in sto:
                    total_planned_points += s.ticket.points

                sp.total_points_when_started = total_planned_points
                time_start = timedelta(minutes=datetime.now().minute,
                                       hours=datetime.now().hour)
                time_end = timedelta(minutes=59, hours=23)
                sp.start_date = parser.parse(
                    data.get('start_date')) + time_start
                sp.end_date = parser.parse(data.get('end_date')) + time_end
                sp.started = True
            elif data.get('for_finalized'):
                sp.finalized = True
                tt = TicketColumnTransition.objects(sprint=sp,
                                                    latest_state=True)
                finished_tickets = []
                for t in tt:
                    if t.column.done_column:
                        finished_tickets.append(t.ticket)

                all_not_finised = SprintTicketOrder.objects(ticket__nin=finished_tickets,
                                                            sprint=sp,
                                                            active=True)
                all_not_finised.update(set__active=False)

            sp.save()
            # # add to redis
            r = RedisClient(channel=str(sp.project.pk))
            r.store('update_sprint', **kwargs)
            return sp.to_json(), 200

        return jsonify({"error": 'Bad Request'}), 400

    def delete(self, sp_id, *args, **kwargs):
        sp = Sprint.objects.get(pk=sp_id)
        sp.delete()
        # # add to redis
        r = RedisClient(channel=str(sp.project.pk))
        r.store('delete_sprint', **kwargs)
        return sp.to_json(), 204


class SprintActive(AuthResource):
    def __init__(self):
        super(SprintActive, self).__init__()

    def get(self, project_pk, *args, **kwargs):
        sprints = Sprint.objects(project=project_pk, started=True,
                                 finalized=False)
        sprint = None
        if sprints:
            sprint = sprints[0]
        if sprint:
            return sprint.to_json(), 200
        return jsonify({'started': False}), 200


class SprintTickets(AuthResource):
    def __init__(self):
        super(SprintTickets, self).__init__()

    def get(self, sprint_id, *args, **kwargs):
        sprint = Sprint.objects.get(pk=sprint_id)
        if sprint:
            return sprint.get_tickets_board_backlog()
        return jsonify({'error': 'Bad Request'}), 400


class SprintChart(AuthResource):
    def __init__(self):
        super(SprintChart, self).__init__()

    def get(self, sprint_id, *args, **kwargs):
        sprint = Sprint.objects.get(pk=sprint_id)
        if sprint:
            duration = sprint.project.sprint_duration
            tickets_in_sprint = SprintTicketOrder.objects(sprint=sprint)
            planned = sprint.total_points_when_started
            ideal_planned = 0
            if tickets_in_sprint:
                for sto in tickets_in_sprint:
                    ideal_planned += sto.ticket.points
            else:
                ideal_planned = planned
            # get done column
            col = Column.objects.get(project=sprint.project,
                                     done_column=True)
            sd = sprint.start_date
            days = []

            starting_points = planned

            points_remaining = []
            ideal = [ideal_planned]
            planned_counter = ideal_planned

            days.append(sd)
            counter = 1

            while len(days) <= duration:
                d = sd + timedelta(days=counter)
                if d.weekday() != 5 and d.weekday() != 6:
                    days.append(d)
                counter += 1

            for day in days:
                planned_counter = (planned_counter - ideal_planned / duration)
                if planned_counter > -1 and len(ideal) < len(days):
                    ideal.append(planned_counter)

                start_date = day
                end_date = start_date + timedelta(hours=23, minutes=59)

                if start_date.date() <= datetime.now().date():

                    tct_list = TicketColumnTransition.objects(column=col,
                                                              sprint=sprint,
                                                              when__gte=start_date.date(),
                                                              when__lt=end_date.date(),
                                                              latest_state=True)
                    points_burned_for_date = 0
                    tickets = []
                    for tct in tct_list:
                        tickets.append(
                            u'- %s-%s (%s)' % (tct.ticket.project.prefix,
                                               tct.ticket.number,
                                               tct.ticket.points))
                        points_burned_for_date += tct.ticket.points
                    starting_points -= points_burned_for_date

                    # tickets after started sprint
                    std = start_date + timedelta(minutes=5)
                    spt_list = SprintTicketOrder.objects(sprint=sprint,
                                                         when__gt=std,
                                                         when__lt=end_date)
                    for spt in spt_list:
                        starting_points += spt.ticket.points
                    points_remaining.append(starting_points)

            # days.insert(0, 'Start')
            data = {
                'points_remaining': points_remaining,
                'dates': days,
                'ideal': ideal,
                'all_tickets': json.loads(
                    sprint.get_tickets_with_latest_status())
            }
            return jsonify(data), 200
        return jsonify({'error': 'Bad Request'}), 400


class SprintArchivedList(AuthResource):
    def __init__(self):
        super(SprintArchivedList, self).__init__()

    def get(self, project_pk, *args, **kwargs):
        return Sprint.objects(project=project_pk, finalized=True).order_by(
            'order').to_json(archived=True)


class SprintAllList(AuthResource):
    def __init__(self):
        super(SprintAllList, self).__init__()

    def get(self, project_pk, *args, **kwargs):
        return Sprint.objects(project=project_pk).order_by('order').to_json()