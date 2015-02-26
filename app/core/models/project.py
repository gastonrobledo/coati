from datetime import datetime

from bson import json_util

from app.core import db
import app.core.models.user as user


PROJECT_TYPE = (('S', 'Scrum'),
                ('K', 'Kanban'))


__all__ = [
    'Project',
    'ProjectMember'
]


class Project(db.BaseDocument):
    name = db.StringField(required=True, unique_with='owner')
    description = db.StringField()
    active = db.BooleanField(default=True)
    owner = db.ReferenceField(user.User,
                              reverse_delete_rule=db.CASCADE)
    prefix = db.StringField()
    sprint_duration = db.IntField()
    project_type = db.StringField(max_length=1,
                                  choices=PROJECT_TYPE,
                                  default='S')

    meta = {
        'indexes': ['name']
    }

    def to_json(self):
        data = self.to_dict()
        if isinstance(self.project_type,
                      bool) and self.project_type:
            data["project_type"] = 'S'
        elif isinstance(self.project_type,
                        bool) and not self.project_type:
            data["project_type"] = 'K'
        data["owner"] = self.owner.to_dict()
        data["owner"]["id"] = str(self.owner.pk)
        data['members'] = ProjectMember.get_members_for_project(self)
        del data["owner"]["_id"]
        return json_util.dumps(data)

    def clean(self):
        if self.owner is None:
            raise db.ValidationError('Owner must be provided')


class ProjectMember(db.BaseDocument):
    member = db.ReferenceField(user.User,
                               reverse_delete_rule=db.CASCADE)
    project = db.ReferenceField(Project,
                                reverse_delete_rule=db.CASCADE)
    since = db.DateTimeField(default=datetime.now())
    is_owner = db.BooleanField(default=False)

    def to_json(self, *args, **kwargs):
        data = self.to_dict()
        data['member'] = self.member.to_dict()
        return json_util.dumps(data)

    @classmethod
    def get_projects_for_member(cls, member_pk):
        prj_mem = cls.objects(member=member_pk)
        projects = []
        for pm in prj_mem:
            if pm.project.active:
                projects.append(pm.project.to_dict())
            elif str(pm.project.owner.pk) == member_pk:
                projects.append(pm.project.to_dict())

        return json_util.dumps(projects)

    @classmethod
    def get_members_for_project(cls, project):
        prj_mem = cls.objects(project=project)
        members = []
        for pm in prj_mem:
            val = pm.to_dict()
            val['member'] = pm.member.to_dict()
            members.append(val)
        return members