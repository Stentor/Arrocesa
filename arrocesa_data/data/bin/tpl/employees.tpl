<odoo>
    <data>
    % for employee in employees:
        <record id="{employee['code']}" model="hr.employee">
            <field name="name">${employee['name']}</field>
            <field name="identification_id">${employee['identification_id']}</field>
            <field name="passport_id">${employee['passport_id']}</field>
            <field name="departement_id" ref="${employee['parent']}"/>
        </record>
        %endif
    % endfor
    </data>
</odoo>

id,name,identification_id,passport_id,country_id,work_email,mobile_phone,department_id/id,job_id/id,resource_calendar_id,cargo_iess/id,discapacitado,mensualize_13,mensualize_14,mensualize_fr,director_sindical,horas_extra