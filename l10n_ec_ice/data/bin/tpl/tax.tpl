<odoo>
    <data>
        % for tax in taxes:
           % if tax['Percent'] != '': 
        <record id="tax_ice${tax['Cod_Imp']}" model="account.tax">
            <field name="name">${tax['Des_Imp']}</field>
            <field name="description">${tax['Cod_Imp']}</field>
            <field name="amount_type">code</field>
            <field name="type_tax_use">sale</field>
            <field name="tax_group_id" ref="l10n_ec_tax.ice"/>
            <field name="amount">0</field>
            <field name="percent_report">${tax['Percent']}</field>
            <field name="python_compute">
                <![CDATA[
base = max(
    product.standard_price*1.25,
    base_amount/(1.0515)
)
if tax.percent_report:
    coeff = tax.percent_report
    result = base*float(coeff)/100.0
else:
    result = 0           
                ]]>
            </field>
        </record>
    % endif
    % endfor
    </data>
</odoo>
