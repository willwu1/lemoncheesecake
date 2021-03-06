import os.path

from lemoncheesecake.project import SimpleProjectConfiguration

###
# Variables
###
project_dir = os.path.dirname(__file__)


###
# Project
###
class MyProjectConfiguration(SimpleProjectConfiguration):
    pass

project = SimpleProjectConfiguration(
    suites_dir=os.path.join(project_dir, "tests"),
    fixtures_dir=os.path.join(project_dir, "fixtures"),
)