<odoo>
    <data>
    % for account in groups:
        % if account['code'] != '':
        <record id="account_group_${account['code']}" model="account.group">
            <field name="code_prefix">${account['code']}</field>
            <field name="name">${account['name']}</field>
            % if account['parent'] != '':
            <field name="parent_id" ref="${account['parent']}"/>
            %endif
        </record>
        %endif
    % endfor
    </data>
</odoo>