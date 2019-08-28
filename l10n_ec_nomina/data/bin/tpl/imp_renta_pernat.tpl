<odoo>
    <data>
    % for impuesto in impuestos:
        % if impuesto['code'] != '':
        <record id="impuesto_${impuesto['code']}" model="hr.impuesto.renta">
            <field name="code">${impuesto['code']}</field>
            <field name="frac_bas">${impuesto['frac_bas']}</field>
            <field name="exceso_hasta">${impuesto['exceso_hasta']}</field>
            <field name="imp_frac_bas">${impuesto['imp_frac_bas']}</field>
            <field name="porc_imp_frac_exc">${impuesto['porc_imp_frac_exc']}</field>
        </record>
        %endif
    % endfor
    </data>
</odoo>