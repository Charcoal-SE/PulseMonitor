import jsonpickle
import tabulate
import BotpySE as bp

# Our own little re wrapper libraryo
import regex as re


class Tag:
    def __init__(self, name, regex, user_id, user_name):
        normalized_regex = re.compile(regex).pattern

        self.name = name
        self.regex = normalized_regex
        self.user_id = user_id
        self.user_name = user_name

        self.format = "[tag:" + self.name + "]"


class TagManager:
    def __init__(self, filename='./tags.json'):
        self.tags = list()
        self.filename = filename

        try:
            with open(filename, 'r') as file_handle:
                tags = jsonpickle.decode(file_handle.read())
            self.tags = tags
        except FileNotFoundError:
            pass

    def add(self, tag):
        self.tags.append(tag)
        self.save()
        return tag

    def remove(self, name):
        for tag in self.tags:
            if tag.name == name:
                self.tags.remove(tag)
                self.save()
                return True
        return False

    def remove_matching(self, expr):
        r = re.compile(expr)
        remove = []
        for tag in self.tags:
            if r.search(tag.regex):
                remove.append(tag)
        for tag in remove:
            self.tags.remove(tag)
        self.save()
        return remove

    def filter_post(self, post):
        tags = list()
        for tag in self.tags:
            if re.search(tag.regex, post):
                tags.append(tag.format)
        return " ".join(tags) + post

    def list(self):
        for tag in self.tags:
            yield tag

    def save(self):
        encoded = jsonpickle.encode(self.tags)
        with open(self.filename, "w") as file_handle:
            file_handle.write(encoded)


class CommandListTags(bp.Command):
    @staticmethod
    def usage():
        return ["listtags", "list tags", "tags", "all tags"]

    def run(self):
        tag_list = list()
        for tag in self.command_manager.tags.list():
            tag_list.append([tag.name, tag.regex, tag.user_name])

        table = tabulate.tabulate(
            tag_list, headers=["Name", "Regex", "Added By"], tablefmt="orgtbl")

        self.post("    " + re.sub('\n', '\n    ', table), False)


class CommandAddTag(bp.Command):
    @staticmethod
    def usage():
        # Regexes may have a space; thus last part of usage is always "..."
        return [
            "addtag * ...", "add tag * ...",
            "add tag with name * and regex ...",
            "add tag * matching ...",
            "add tag * for ..."]

    def privileges(self):
        return 1

    def run(self):
        user_id = self.message.user.id
        user_name = self.message.user.name

        tag_name = self.arguments[0]

        if len(self.arguments) == 1:
            self.reply('Need two arguments: tag and regex')
            return

        regex = ' '.join(self.arguments[1:])

        try:
            newtag = self.command_manager.tags.add(
                Tag(tag_name, regex, user_id, user_name))
            self.reply("Added [tag:{0}] for regex {1}".format(
                newtag.name, newtag.regex))
        except re.error as err:
            self.reply("Could not add tag for regex {0}: {1}".format(
                regex, err))


class CommandRemoveTag(bp.Command):
    @staticmethod
    def usage():
        return [
            "removetag ...", "remove tag ...", "rmtag ...",
            "delete tag ...", "destroy tag ...",
            "poof tag ...", "deletetag ..."]

    def privileges(self):
        return 1

    def run(self):
        regex = ' '.join(self.arguments)

        try:
            removed = self.command_manager.tags.remove_matching(regex)
        except re.error as re_err:
            self.reply("Could not remove tag for regex `{0}`: `{1}`".format(
                regex, re_err))
            return

        if not removed:
            self.reply("No tag found with regex `{0}`".format(regex))
            return
        self.reply("Removed {0} tags matching regex `{1}`.".format(
            len(removed), regex))
