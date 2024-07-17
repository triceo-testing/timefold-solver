from dataclasses import dataclass, field
from decimal import Decimal
from timefold.solver import *
from timefold.solver.config import *
from timefold.solver.domain import *
from timefold.solver.score import *
from typing import Annotated

def test_simple_score():
    uninit_score = SimpleScore(10, init_score=-2)
    score = SimpleScore.of(10)

    assert str(uninit_score) == '-2init/10'
    assert str(score) == '10'

    assert SimpleScore.parse('-2init/10') == uninit_score
    assert SimpleScore.parse('10') == score


def test_hard_soft_score():
    uninit_score = HardSoftScore(100, 20, init_score=-3)
    score = HardSoftScore.of(100, 20)

    assert str(uninit_score) == '-3init/100hard/20soft'
    assert str(score) == '100hard/20soft'

    assert HardSoftScore.parse('-3init/100hard/20soft') == uninit_score
    assert HardSoftScore.parse('100hard/20soft') == score


def test_hard_medium_soft_score():
    uninit_score = HardMediumSoftScore(1000, 200, 30, init_score=-4)
    score = HardMediumSoftScore.of(1000, 200, 30)

    assert str(uninit_score) == '-4init/1000hard/200medium/30soft'
    assert str(score) == '1000hard/200medium/30soft'

    assert HardMediumSoftScore.parse('-4init/1000hard/200medium/30soft') == uninit_score
    assert HardMediumSoftScore.parse('1000hard/200medium/30soft') == score


def test_bendable_score():
    uninit_score = BendableScore((1, -2, 3), (-30, 40), init_score=-500)
    score = BendableScore.of((1, -2, 3), (-30, 40))

    assert str(uninit_score) == '-500init/[1/-2/3]hard/[-30/40]soft'
    assert str(score) == '[1/-2/3]hard/[-30/40]soft'

    assert BendableScore.parse('-500init/[1/-2/3]hard/[-30/40]soft') == uninit_score
    assert BendableScore.parse('[1/-2/3]hard/[-30/40]soft') == score


def test_simple_decimal_score():
    uninit_score = SimpleDecimalScore(Decimal('10.1'), init_score=-2)
    score = SimpleDecimalScore.of(Decimal('10.1'))

    assert str(uninit_score) == '-2init/10.1'
    assert str(score) == '10.1'

    assert SimpleDecimalScore.parse('-2init/10.1') == uninit_score
    assert SimpleDecimalScore.parse('10.1') == score


def test_hard_soft_decimal_score():
    uninit_score = HardSoftDecimalScore(Decimal('100.1'), Decimal('20.2'), init_score=-3)
    score = HardSoftDecimalScore.of(Decimal('100.1'), Decimal('20.2'))

    assert str(uninit_score) == '-3init/100.1hard/20.2soft'
    assert str(score) == '100.1hard/20.2soft'

    assert HardSoftDecimalScore.parse('-3init/100.1hard/20.2soft') == uninit_score
    assert HardSoftDecimalScore.parse('100.1hard/20.2soft') == score


def test_hard_medium_soft_decimal_score():
    uninit_score = HardMediumSoftDecimalScore(Decimal('1000.1'), Decimal('200.2'), Decimal('30.3'), init_score=-4)
    score = HardMediumSoftDecimalScore.of(Decimal('1000.1'), Decimal('200.2'), Decimal('30.3'))

    assert str(uninit_score) == '-4init/1000.1hard/200.2medium/30.3soft'
    assert str(score) == '1000.1hard/200.2medium/30.3soft'

    assert HardMediumSoftDecimalScore.parse('-4init/1000.1hard/200.2medium/30.3soft') == uninit_score
    assert HardMediumSoftDecimalScore.parse('1000.1hard/200.2medium/30.3soft') == score


def test_bendable_decimal_score():
    uninit_score = BendableDecimalScore((Decimal('1.1'), Decimal('-2.2'), Decimal('3.3')),
                                        (Decimal('-30.3'), Decimal('40.4')), init_score=-500)
    score = BendableDecimalScore.of((Decimal('1.1'), Decimal('-2.2'), Decimal('3.3')),
                                    (Decimal('-30.3'), Decimal('40.4')))

    print(str(uninit_score))
    assert str(uninit_score) == '-500init/[1.1/-2.2/3.3]hard/[-30.3/40.4]soft'
    assert str(score) == '[1.1/-2.2/3.3]hard/[-30.3/40.4]soft'

    assert BendableDecimalScore.parse('-500init/[1.1/-2.2/3.3]hard/[-30.3/40.4]soft') == uninit_score
    assert BendableDecimalScore.parse('[1.1/-2.2/3.3]hard/[-30.3/40.4]soft') == score


def test_sanity_score_type():
    @planning_entity
    @dataclass
    class Entity:
        value: Annotated[int | None, PlanningVariable] = field(default=None)

    for score_type, score_value in (
            (SimpleScore, SimpleScore.ONE),
            (HardSoftScore, HardSoftScore.ONE_HARD),
            (HardMediumSoftScore, HardMediumSoftScore.ONE_HARD),
            (BendableScore, BendableScore.of((1, ), (0, ))),
            (SimpleDecimalScore, SimpleDecimalScore.ONE),
            (HardSoftDecimalScore, HardSoftDecimalScore.ONE_HARD),
            (HardMediumSoftDecimalScore, HardMediumSoftDecimalScore.ONE_HARD),
            (BendableDecimalScore, BendableDecimalScore.of((Decimal(1), ), (Decimal(0), )))
    ):
        score_annotation = PlanningScore
        if score_type == BendableScore or score_type == BendableDecimalScore:
            score_annotation = PlanningScore(bendable_hard_levels_size=1,
                                             bendable_soft_levels_size=1)

        @planning_solution
        @dataclass
        class Solution:
            entities: Annotated[list[Entity], PlanningEntityCollectionProperty]
            values: Annotated[list[int], ValueRangeProvider]
            score: Annotated[score_type | None, score_annotation] = field(default=None)

        @constraint_provider
        def constraints(constraint_factory: ConstraintFactory):
            return [
                constraint_factory.for_each(Entity)
                .reward(score_value)
                .as_constraint('Minimize value')
            ]

        solver_config = SolverConfig(
            solution_class=Solution,
            entity_class_list=[Entity],
            score_director_factory_config=ScoreDirectorFactoryConfig(
                constraint_provider_function=constraints
            ),
            termination_config=TerminationConfig(
                best_score_limit=str(score_value)
            )
        )

        solver_factory = SolverFactory.create(solver_config)
        solver = solver_factory.build_solver()
        problem = Solution(entities=[Entity()],
                           values=[1])
        solution = solver.solve(problem)
        assert solution.entities[0].value == 1
        assert solution.score == score_value


def test_simple_decimal_score_domain():
    @planning_entity
    @dataclass
    class Entity:
        value: Annotated[Decimal | None, PlanningVariable] = field(default=None)

    @planning_solution
    @dataclass
    class Solution:
        entities: Annotated[list[Entity], PlanningEntityCollectionProperty]
        values: Annotated[list[Decimal], ValueRangeProvider]
        score: Annotated[SimpleDecimalScore | None, PlanningScore] = field(default=None)


    @constraint_provider
    def constraints(constraint_factory: ConstraintFactory):
        return [
            constraint_factory.for_each(Entity)
                .penalize_decimal(SimpleDecimalScore.of(Decimal('0.1')), lambda e: e.value)
                .as_constraint('Minimize value')
        ]

    solver_config = SolverConfig(
        solution_class=Solution,
        entity_class_list=[Entity],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=constraints
        ),
        termination_config=TerminationConfig(
            best_score_limit='-0.2'
        )
    )

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()
    problem = Solution(entities=[Entity() for i in range(2)],
                       values=[Decimal(1), Decimal(2), Decimal(3)])
    solution = solver.solve(problem)
    assert solution.entities[0].value == 1
    assert solution.entities[1].value == 1
    assert solution.score == SimpleDecimalScore.of(Decimal('-0.2'))
