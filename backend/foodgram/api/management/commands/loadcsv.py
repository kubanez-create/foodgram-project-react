"""Custom manage.py command for loading csv files into project database."""
import csv

from api.models import Ingredients, Recipes, Tags
from django.core.management.base import BaseCommand, CommandError
from users.models import CustomUser

COMMANDS = {
    "tags": Tags,
    "ingredients": Ingredients,
    "recipes": Recipes,
    "users": CustomUser,
}


class Command(BaseCommand):
    help = (
        "The command for loading csv files into projects db."
        " Takes command-line arguments. For example to load"
        "file genre.csv you need to enter the following command:"
        " python manage.py loadcsv review"
        " /home/kubanez/Dev/api_yamdb/api_yamdb/static/data/review.csv."
        " Also you need to load files in order:\n"
        "first - files with models without foreign keys ( genre"
        " category, user, title)\n"
        "then - models with them ( titles, genre_title, review and comment)"
    )

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("command", nargs="+", type=str)
        parser.add_argument("filename", nargs="+", type=str)

    def handle(self, *args, **options):
        command: str = options["command"][0]
        filename: str = options["filename"][0]

        try:
            model = COMMANDS.get(command)
            with open(filename) as f:
                reader = csv.reader(f)
                field_names = next(reader)

                for row in reader:
                    data_to_insert = dict(zip(field_names, row, strict=True))
                    special_models = ["recipes"]
                    if command not in special_models:
                        model.objects.create(**data_to_insert)
                    # elif command == "titles":
                    #     model.objects.create(
                    #         id=data_to_insert.get("id"),
                    #         name=data_to_insert.get("name"),
                    #         year=data_to_insert.get("year"),
                    #         category=Category.objects.get(
                    #             pk=data_to_insert.get("category")
                    #         ),
                    #     )

            self.stdout.write(
                self.style.SUCCESS('Successfully loaded the file "%s"' % filename)
            )
        except IOError:
            raise CommandError("File '%s' does not exist" % filename) from None
