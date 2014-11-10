from flask.ext.restful import Api
from resources.sprint import SprintList, SprintInstance, SprintOrder
from resources.project import ProjectList, ProjectInstance
from resources.ticket import TicketBacklogList, TicketSprintList, \
    TicketOrderBacklogList
from resources.user import UsersList, UserInstance
from app.utils import output_json


def init_app(app, decorators=None):
    api = Api(app,
              default_mediatype='application/json',
              decorators=decorators)
    api.add_resource(ProjectList, '/api/projects')
    api.add_resource(ProjectInstance, '/api/project/<string:slug>')
    api.add_resource(UsersList, '/api/users')
    api.add_resource(UserInstance, '/api/user/<string:pk>')
    api.add_resource(SprintList, '/api/sprints/<string:project_pk>')
    api.add_resource(SprintOrder, '/api/sprints/<string:project_pk>/order')
    api.add_resource(SprintInstance, '/api/sprint/<string:sp_id>')
    api.add_resource(TicketBacklogList, '/api/tickets/<string:project_pk>')
    api.add_resource(TicketOrderBacklogList, '/api/tickets/<string:project_pk>/order')
    api.add_resource(TicketSprintList, '/api/tickets/sprint/<string:sprint_pk>')
    api.representations = {'application/json': output_json}