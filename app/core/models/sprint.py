from datetime import datetime

from bson import json_util
from mongoengine import DoesNotExist

from app.core import db
import app.core.models.column as column
import app.core.models.comment as comment
import app.core.models.project as project
import app.core.models.ticket as ticket


__all__ = [
    'Sprint',
    'SprintTicketOrder'
]


class Sprint(db.BaseDocument):
    name = db.StringField(max_length=100, required=True)
    start_date = db.DateTimeField()
    end_date = db.DateTimeField()
    project = db.ReferenceField(project.Project,
                                reverse_delete_rule=db.CASCADE)
    order = db.IntField(min_value=0)
    started = db.BooleanField(default=False)
    finalized = db.BooleanField(default=False)
    total_points_when_started = db.IntField()

    def to_json(self, *args, **kwargs):
        data = self.to_dict()

        tickets = SprintTicketOrder.objects(sprint=self.pk,
                                            active=kwargs.get('archived', False)).order_by('order')

        ticket_list = []
        for t in tickets:
            tkt = t.ticket_repr
            tkt['order'] = t.order
            tkt['badges'] = {
                'comments': comment.Comment.objects(ticket=t.ticket).count(),
                'files': len(t.ticket.files)
            }
            assignments = []
            for ass in t.ticket.assigned_to:
                if ass.__class__.__name__ != 'DBRef':
                    assignments.append(ass.to_dict())
            tkt['assigned_to'] = assignments
            ticket_list.append(tkt)
        data["tickets"] = ticket_list
        return json_util.dumps(data)

    def clean(self):
        if self.project is None:
            raise db.ValidationError('Project must be provided')

    def get_tickets_with_latest_status(self):
        tickets = SprintTicketOrder.objects(sprint=self).order_by('order')
        result_list = []
        for t in tickets:
            assignments = []
            for ass in t.ticket.assigned_to:
                if ass.__class__.__name__ != 'DBRef':
                    assignments.append(ass.to_dict())
            tkt = t.ticket_repr
            value = {
                'points': tkt.get('points'),
                'title': '%s-%s: %s' % (t.ticket.project.prefix,
                                        tkt.get('number'),
                                        tkt.get('title')),
                '_id': t.ticket.id,
                'type': tkt.get('type'),
                'added_after': t.when > self.start_date,
                'number': tkt.get('number')
            }
            try:
                tt = column.TicketColumnTransition.objects.get(ticket=t.ticket,
                                                        latest_state=True)
                value['who'] = tt.who.to_dict()
                value['when'] = tt.when
                value['where'] = tt.column.title
                if tt.column.done_column:
                    value['finished'] = True
                else:
                    value['finished'] = False
            except DoesNotExist:
                value['finished'] = False

            result_list.append(value)
        return json_util.dumps(result_list)


    def get_tickets_board_backlog(self):
        # first get all the columns
        columns = column.Column.objects(project=self.project)
        ticket_transitions = column.TicketColumnTransition.objects(column__in=columns,
                                                            latest_state=True)
        tickets_in_cols = []
        for tt in ticket_transitions:
            tickets_in_cols.append(tt.ticket)

        # exclude from sprint
        tickets = SprintTicketOrder.objects(sprint=self,
                                            active=True,
                                            ticket__nin=tickets_in_cols)\
            .order_by('order')
        ticket_list = []
        for t in tickets:
            if t.ticket.__class__.__name__ != 'DBRef':
                tkt = t.ticket_repr
                tkt['order'] = t.order
                tkt['badges'] = {
                    'comments': comment.Comment.objects(ticket=t.ticket).count(),
                    'files': len(t.ticket.files)
                }
                assignments = []
                for ass in t.ticket.assigned_to:
                    if ass.__class__.__name__ != 'DBRef':
                        val = ass.to_dict()
                        val['member'] = ass.member.to_dict()
                        assignments.append(val)
                tkt['assigned_to'] = assignments
                ticket_list.append(tkt)
        return json_util.dumps(ticket_list)


class SprintTicketOrder(db.BaseDocument):
    ticket = db.ReferenceField(ticket.Ticket,
                               reverse_delete_rule=db.CASCADE)
    ticket_repr = db.DictField()
    order = db.IntField()
    sprint = db.ReferenceField(Sprint,
                               reverse_delete_rule=db.CASCADE)
    active = db.BooleanField(default=True)
    when = db.DateTimeField(default=datetime.now())