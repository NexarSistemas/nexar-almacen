### REEMPLAZAR la función licencia() en app.py
### Buscar:
###   @app.route('/licencia')
###   @login_required
###   def licencia():
###       status     = db.get_demo_status()
###       machine_id = db.get_machine_id()
###       lic_info   = db.get_license_info() if not status['demo'] else None
###       return render_template('licencia.html',
###                              status=status,
###                              machine_id=machine_id,
###                              lic_info=lic_info)
###
### Reemplazar con:

@app.route('/licencia')
@login_required
def licencia():
    status     = db.get_demo_status()
    machine_id = db.get_machine_id()
    lic_info   = db.get_license_info() if not status['demo'] else None

    # Calcular uso actual para mostrar barras de progreso en plan Básico
    tier_limits = {}
    if lic_info and lic_info.get('tier') == 'BASICA':
        r_off  = db.q(
            "SELECT COUNT(*) FROM productos WHERE activo=1 "
            "AND codigo_barras != '' "
            "AND (codigo_barras LIKE '779%' OR codigo_barras LIKE '780%')",
            fetchone=True
        )
        r_cli  = db.q("SELECT COUNT(*) FROM clientes WHERE activo=1", fetchone=True)
        r_prov = db.q("SELECT COUNT(*) FROM proveedores WHERE activo=1", fetchone=True)
        tier_limits = {
            'productos_off_actual': r_off[0]  if r_off  else 0,
            'clientes_actual':      r_cli[0]  if r_cli  else 0,
            'proveedores_actual':   r_prov[0] if r_prov else 0,
        }

    return render_template('licencia.html',
                           status=status,
                           machine_id=machine_id,
                           lic_info=lic_info,
                           tier_limits=tier_limits)
