<odoo>
    <data>
    % for ram in ramas:
        % if ram['code'] != '':
        <record id="rama_${ram['rama_ids/code']}" model="iess.sectorial.rama">
            <field name="code">${ram['rama_ids/code']}</field>
            <field name="name">${ram['rama_ids/name']}</field>
            <field name="comision_id" ref="comision_${ram['code']}" />
        </record>
        %endif
    % endfor
    </data>
</odoo>