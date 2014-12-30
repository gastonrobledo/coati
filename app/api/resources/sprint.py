

__author__ = 'gastonrobledo'
import json
from datetime import timedelta, datetime

from dateutil import parser
from flask import jsonify, request
from flask.ext.restful import Resource

from app.schemas import (Sprint, Project, SprintTicketOrder,
                         Column, TicketColumnTransition)

from app.redis import RedisClient


class SprintOrder(Resource):
    def __init__(self):
        super(SprintOrder, self).__init__()

    def post(self, project_pk, *args, **kwargs):
        data = request.get_json(force=True, silent=True)
        if data:
            for index, s in enumerate(data):
                sprint = Sprint.objects.get(pk=s)
                sprint.order = index
                sprint.save()
            ## add to redis
            r = RedisClient(channel=project_pk)
            r.store(dict(type='order_sprints', data=data))
            return jsonify({'success': True}), 200
        return jsonify({"error": 'Bad Request'}), 400


class SprintList(Resource):
    def __init__(self):
        super(SprintList, self).__init__()

    def get(self, project_pk, *args, **kwargs):
        return Sprint.objects(project=project_pk).order_by('order').to_json()

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
        ## add to redis
        r = RedisClient(channel=project_pk)
        r.store(dict(type='new_sprint', data=sp.to_json()))
        return sp.to_json(), 201


class SprintInstance(Resource):
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
                sto = SprintTicketOrder.objects(sprint=sp)
                total_planned_points = 0
                for s in sto:
                    total_planned_points += s.ticket.points

                sp.total_points_when_started = total_planned_points
                sp.start_date = parser.parse(data.get('start_date'))
                sp.end_date = parser.parse(data.get('end_date'))
                sp.started = True
            elif data.get('for_finalized'):
                sp.finalized = True

            sp.save()
            ## add to redis
            r = RedisClient(channel=str(sp.project.pk))
            r.store(dict(type='update_sprint', data=sp.to_json()))
            return sp.to_json(), 200
        return jsonify({"error": 'Bad Request'}), 400

    def delete(self, sp_id, *args, **kwargs):
        sp = Sprint.objects.get(pk=sp_id)
        sp.delete()
        ## add to redis
        r = RedisClient(channel=str(sp.project.pk))
        r.store(dict(type='delete_sprint', data=sp.to_json()))
        return sp.to_json(), 204


class SprintActive(Resource):
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


class SprintTickets(Resource):
    def __init__(self):
        super(SprintTickets, self).__init__()

    def get(self, sprint_id, *args, **kwargs):
        sprint = Sprint.objects.get(pk=sprint_id)
        if sprint:
            return sprint.get_tickets_board_backlog()
        return jsonify({'error': 'Bad Request'}), 400


class SprintChart(Resource):
    def __init__(self):
        super(SprintChart, self).__init__()

    def get(self, sprint_id, *args, **kwargs):
        sprint = Sprint.objects.get(pk=sprint_id)
        if sprint:
            duration = sprint.project.sprint_duration
            planned = sprint.total_points_when_started
            # get done column
            col = Column.objects.get(project=sprint.project,
                                     done_column=True)
            sd = sprint.start_date
            days = []

            starting_points = planned

            points_remaining = []
            tickets_per_day = []
            ideal = [planned]
            planned_counter = planned

            days.append(sd)
            counter = 1

            while len(days) <= duration:
                d = sd + timedelta(days=counter)
                if d.weekday() != 5 and d.weekday() != 6:
                    days.append(d)
                counter += 1

            for day in days:
                planned_counter = (planned_counter - planned / duration)
                if planned_counter > -1:
                    ideal.append(planned_counter)
                start_date = day
                end_date = start_date + timedelta(days=1)

                if start_date.date() <= datetime.now().date():

                    tct_list = TicketColumnTransition.objects(column=col,
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
                    spt_list = SprintTicketOrder.objects(sprint=sprint,
                                                         when__gte=start_date.date(),
                                                         when__lt=end_date.date())
                    for spt in spt_list:
                        tickets.append(
                            u'+ %s-%s  (%s)' % (spt.ticket.project.prefix,
                                                spt.ticket.number,
                                                spt.ticket.points))
                        starting_points += spt.ticket.points

                    tickets_per_day.append(tickets)
                    points_remaining.append(starting_points)

            # days.insert(0, 'Start')
            data = {
                'points_remaining': points_remaining,
                'dates': days,
                'tickets_per_day': tickets_per_day,
                'ideal': ideal,
                'all_tickets': json.loads(sprint.get_tickets_with_latest_status())
            }
            return jsonify(data), 200
        return jsonify({'error': 'Bad Request'}), 400