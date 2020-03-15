import pytest

from pkg_resources import Requirement as R

from pyp2rpm.dependency_parser import dependency_to_rpm


class TestDependencyParser():

    @pytest.mark.parametrize(('d', 'r', 'rich', 'expected'), [
        ('docutils>=0.3,<1,!=0.5', True, False,
         [['Requires', 'docutils', '{name} >= 0.3'],
          ['Requires', 'docutils', '{name} < 1'],
          ['Conflicts', 'docutils', '{name} = 0.5']
          ]
         ),
        ('pytest>=0.3a5,<1.1.1.1,!=1', False, False,
         [['BuildRequires', 'pytest', '{name} >= 0.3~a5'],
          ['BuildRequires', 'pytest', '{name} < 1.1.1.1'],
          ['BuildConflicts', 'pytest', '{name} = 1']
          ]
         ),
        ('pyp2rpm~=3.3.0rc2', True, False,
         [['Requires', 'pyp2rpm', '{name} >= 3.3~rc2'],
          ['Requires', 'pyp2rpm', '{name} < 3.4']
         ]
         ),
        ('pyp2rpm~=0.9.3', True, False,
         [['Requires', 'pyp2rpm', '{name} >= 0.9.3'],
          ['Requires', 'pyp2rpm', '{name} < 0.10']
         ]
         ),
        ('pyp2rpm~=0.9.3.1', True, False,
         [['Requires', 'pyp2rpm', '{name} >= 0.9.3.1'],
          ['Requires', 'pyp2rpm', '{name} < 0.9.4']
         ]
         ),
        ('docutils>=0.3,<1,!=0.5', True, True,
         [['Requires', 'docutils',
           '({name} >= 0.3 with {name} < 1 with ({name} < 0.5 or {name} > 0.5))']
          ]
         ),
        ('pytest>=0.3a5,<1.1.1.1,!=1', False, True,
         [['BuildRequires', 'pytest',
           '({name} >= 0.3~a5 with {name} < 1.1.1.1 with ({name} < 1 or {name} > 1))']
          ]
         ),
        ('pyp2rpm~=3.3.0rc2', True, True,
         [['Requires', 'pyp2rpm', '({name} >= 3.3~rc2 with {name} < 3.4)']]
         ),
        ('pyp2rpm~=0.9.3', True, True,
         [['Requires', 'pyp2rpm', '({name} >= 0.9.3 with {name} < 0.10)']]
         ),
        ('pyp2rpm~=0.9.3.1', True, True,
         [['Requires', 'pyp2rpm', '({name} >= 0.9.3.1 with {name} < 0.9.4)']]
         ),

    ])
    def test_dependency_to_rpm(self, d, r, rich, expected):
        # we can't convert lists of lists into sets => compare len and contents
        rpm_deps = dependency_to_rpm(R.parse(d), r, rich)
        for dep in expected:
            assert dep in rpm_deps
        assert len(expected) == len(rpm_deps)
