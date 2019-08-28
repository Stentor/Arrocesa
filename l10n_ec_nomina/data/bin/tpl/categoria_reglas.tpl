<odoo>
    <data>
    % for cat in categorias:
        % if cat['category_ids/code'] != '':
        <record id="rule_cat_${cat['category_ids/code']}" model="hr.salary.rule.category">
            <field name="code">${cat['category_ids/code']}</field>
            <field name="name">${cat['category_ids/name']}</field>
            % if cat['category_ids/padre/code'] != '':
            <field name="parent_id" ref="rule_cat_${cat['category_ids/padre/code']}" />
            % endif
        </record>
        %endif
    % endfor
    </data>
</odoo>
