{%- filter md_escape_for_table -%}
{%- set nodes = schema.nodes_from_root | list -%}
{%- if nodes | length > 1 -%}
  {%- for node in nodes[1:] -%}
    {{ node.name_for_breadcrumbs }}{%- if not loop.last %}.{% endif -%}
  {%- endfor -%}
{%- else -%}
  {{ schema.name_for_breadcrumbs }}
{%- endif -%}
{%- endfilter -%}
