<odoo>
    <data>
    % for com in comisiones:
        % if com['code'] != '':
        <record id="comision_${com['code']}" model="iess.sectorial.comision">
            <field name="code">${com['code']}</field>
            <field name="name">${com['name']}</field>
        </record>
        %endif
    % endfor
    </data>
</odoo>