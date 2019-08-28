<odoo>
    <data>
    % for cat in categorias:
        % if cat['category_ids/padre/code'] != '':
        <record id="rule_cat_${cat['category_ids/padre/code']}" model="hr.salary.rule.category">
            <field name="code">${cat['category_ids/padre/code']}</field>
            <field name="name">${cat['category_ids/padre/name']}</field>
        </record>
        %endif
    % endfor
    </data>
</odoo>
