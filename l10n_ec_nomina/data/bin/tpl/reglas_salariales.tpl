<odoo>
    <data>
    % for rule in reglas:
        % if rule['code'] != '':
        <record id="rule_${rule['code']}" model="hr.salary.rule">
            <field name="code">${rule['code']}</field>
            <field name="name">${rule['name']}</field>
            <field name="category_id" ref="rule_cat_${rule['category_ids/code']}"></field>
            <field name="active">${rule['activo']}</field>
            <field name="sequence">${rule['secuencia']}</field>
            <field name="appears_on_payslip">${rule['appear_nom']}</field>
            <field name="condition_select">${rule['condition_based']}</field>
            <field name="condition_python">${rule['condicion_python']}</field>
            <field name="amount_select">${rule['imp_type']}</field>
            <field name="amount_percentage_base">${rule['porcentaje_basado_en']}</field>
            <field name="quantity">${rule['cantidad']}</field>
            <field name="amount_percentage">${rule['porcentaje']}</field>
            <field name="amount_fix">${rule['importe_fijo']}</field>
            <field name="amount_python_compute"><![CDATA[${rule['codigo_python']}]]></field>
            
        </record>
        % endif
    % endfor
    </data>
</odoo>