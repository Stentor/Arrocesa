<odoo>
    <data>
         <record model="account.account.type" id="data_account_type_capital">
            <field name="name">Capital</field>
            <field name="type">other</field>
            <field name="internal_group">asset</field>
            <field name="include_initial_balance" eval="True"/>
        </record>
        <record model="account.account.type" id="data_account_type_stock">
            <field name="name">Inventario</field>
            <field name="type">other</field>
            <field name="internal_group">asset</field>
            <field name="include_initial_balance" eval="True"/>
        </record>
        
        <record id="arrocesa_chart_template" model="account.chart.template">
            <field name="name">Arrocesa - Chart of Accounts</field>
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
            <field name="reconcile">${account['reconcile']}</field>
            <field name="chart_template_id" ref="arrocesa_chart_template"/>
        </record>
        %endif
    % endfor

       <record id="arrocesa_chart_template" model="account.chart.template">
            <field name="property_account_receivable_id" ref="account_account_101020101"/>
            <field name="property_account_payable_id" ref="account_account_201010104"/>
        </record>   
    </data>
</odoo>