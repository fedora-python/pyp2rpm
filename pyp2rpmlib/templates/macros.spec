{%- macro one_dep(dep, python_version) %}
{{ dep[0] }}:{{ ' ' * (15 - dep[0]|length) }}{{ dep[1]|for_python_version(python_version) }}{% if dep[2] is defined %} {{ dep[2] }} {{ dep[3] }}{% endif %}
{%- endmacro %}

{%- macro dependencies(deps, runtime, python_version) %}
  {%- if deps|length > 0 or not runtime %} {# for build deps, we always have at least 1 - pythonXX-devel #}
    {%- if python_version %}
%if %{?with_python{{ python_version }}}
    {%- endif %}
    {%- if not runtime %}
BuildRequires:  python{{ python_version }}-devel
    {%- endif %}
    {%- for dep in deps -%}
{{ one_dep(dep, python_version) }}
    {%- endfor %}
    {%- if python_version %}
%endif # if with_python{{ pv }}
    {%- endif %}
  {%- endif %}
{%- endmacro %}
