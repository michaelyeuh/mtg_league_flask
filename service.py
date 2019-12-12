from models import CommandersModel, UserDraftingModel


class CommanderService:
    def __init__(self):
        self.model = CommandersModel()

    def create(self, params):
        self.model.create(params)

    def delete(self, commander_id):
        return self.model.delete(commander_id)

    def select(self):
        response = self.model.select()
        return response


class DraftingService:
    def __init__(self):
        self.model = UserDraftingModel()

    def userid(self, username):
        user_id = self.model.get_user_id(username)
        return user_id

    def usercomm(self, user_id):
        response = self.model.check_usercomm(user_id)
        return response

    def draft(self, user_id):
        commander = self.model.draft_commander(user_id)
        if commander:
            return commander
        else:
            return "No Commanders Available"
