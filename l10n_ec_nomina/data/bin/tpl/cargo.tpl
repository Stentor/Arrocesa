<odoo>
    <data>
    % for cargo in cargos:
        % if cargo['code'] != '':
        <record id="cargo_${cargo['cargos_ids/code']}" model="iess.sectorial.cargo">
            <field name="code">${cargo['cargos_ids/code']}</field>
            <field name="name">${cargo['cargos_ids/name']}</field>
            <field name="value">${'{0:.2f}'.format(float(cargo['cargos_ids/value'].replace(',','.')))}</field>
            <field name="rama_id" ref="rama_${cargo['rama_ids/code']}" />
        </record>
        %endif
    % endfor
    </data>
</odoo>