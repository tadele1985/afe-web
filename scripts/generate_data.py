from random import randint

from faker import Faker

from core.models import Location, OperationPlan, OperationType, Sector


def generate_operation_plans():
    fake = Faker()
    sectors = Sector.objects.all()
    operation_types = OperationType.objects.all()
    branches = Location.objects.filter(type="BRANCH").all()
    for sector in sectors:
        op_type = operation_types[randint(0, len(operation_types) - 1)]
        for branch in branches:
            forest_site = branch.children.first()
            block = forest_site.children.first()
            comparment = block.children.first()
            sub_comparment = comparment.children.first()
            if sub_comparment is None:
                sub_comparment = Location(
                    name=f"Sub Compartment {fake.name()}",
                    type="SUB_COMPARTMENT",
                    parent=comparment,
                )
            for i in range(5):
                OperationPlan.objects.create(
                    year=i,
                    sector=sector,
                    op_type=op_type,
                    branch=branch,
                    forest_site=forest_site,
                    block=block,
                    comparment=comparment,
                    sub_comparment=sub_comparment,
                    start_date=fake.date(),
                    end_date=fake.date(),
                )


if __name__ == "__main__":
    generate_operation_plans()
