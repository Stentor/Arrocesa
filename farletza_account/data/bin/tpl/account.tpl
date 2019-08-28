<odoo>
    <data>
        <record id="farletza_chart_template" model="account.chart.template">
            <field name="name">Farletza - Chart of Accounts</field>
            <field name="currency_id" ref="base.USD"/>
            <field name="bank_account_code_prefix"></field>
            <field name="cash_account_code_prefix"></field>
            <field name="transfer_account_code_prefix"></field>
        </record>
    % for account in accounts:
        % if account['code'] != '':
        <record id="account_account_${account['code']}" model="account.account.template">
            <field name="code">${account['code']}</field>
            <field name="name">${account['name']}</field>
            <field name="user_type_id" ref="${account['type']}"/>
            <field name="group_id" ref="${account['group']}"/>
            <field name="reconcile">${account['deprecated']}</field>
            <field name="chart_template_id" ref="farletza_chart_template"/>
        </record>
        %endif
    % endfor
    </data>
</odoo>