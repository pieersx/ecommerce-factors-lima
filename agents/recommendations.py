IMPACT_GROUPS = {
    "T06": ("Compra", "Sin catalogo claro, el usuario no puede iniciar una compra verificable."),
    "T07": ("Compra", "Sin ficha de producto completa, la decision de compra queda incompleta."),
    "T08": ("Compra", "Sin precio o disponibilidad, la oferta comercial no es transparente."),
    "T09": ("Compra", "Sin carrito o checkout visible, no se observa un flujo de compra."),
    "T10": ("Compra", "Sin medios de pago declarados, aumenta la friccion antes del checkout."),
    "O01": ("Confianza", "La privacidad es una senal basica de cumplimiento y confianza."),
    "O03": ("Confianza", "Los terminos reducen incertidumbre sobre condiciones de compra."),
    "O06": ("Confianza", "Las devoluciones reducen riesgo percibido por el cliente."),
    "O10": ("Confianza", "La identificacion legal permite reconocer al responsable del comercio."),
    "C02": ("Confianza", "Las senales de seguridad ayudan a sostener confianza en el pago."),
    "O04": ("Operacion", "La politica de envio explica como se cumple la entrega."),
    "O05": ("Operacion", "Costo y plazo de entrega afectan la decision final de compra."),
    "O08": ("Operacion", "El contacto visible permite resolver dudas y reclamos."),
    "O09": ("Operacion", "El soporte rapido reduce abandono y mejora atencion."),
    "A01": ("Operacion", "La cobertura evita expectativas incorrectas sobre entrega."),
    "T02": ("Experiencia", "La experiencia movil es critica para navegacion y conversion."),
    "T03": ("Experiencia", "El rendimiento afecta permanencia y conversion."),
    "T04": ("Experiencia", "La navegacion ayuda a descubrir productos y categorias."),
    "T05": ("Experiencia", "El buscador acelera la ubicacion de productos."),
    "C01": ("Experiencia", "Las resenas reducen incertidumbre en productos y servicio."),
    "C06": ("Experiencia", "La accesibilidad amplia el acceso y mejora estructura del sitio."),
}

GROUP_ORDER = {"Compra": 0, "Confianza": 1, "Operacion": 2, "Experiencia": 3, "Otros": 4}
STATUS_ORDER = {"absent": 0, "not_evaluable": 1, "partial": 2, "present": 3}


class RecommendationAgent:
    def generate(self, factors: list[dict]) -> list[dict]:
        recommendations = []
        for factor in factors:
            if factor["status"] == "present":
                continue
            group, reason = IMPACT_GROUPS.get(
                factor["id"],
                ("Otros", "Este factor completa la madurez observable del canal e-commerce."),
            )
            priority = "Alta" if group in {"Compra", "Confianza"} and factor["status"] == "absent" else "Media"
            if factor["status"] == "not_evaluable":
                priority = "Revision"
            recommendations.append(
                {
                    "factor_id": factor["id"],
                    "factor": factor["name"],
                    "dimension": factor["dimension"],
                    "status": factor["status"],
                    "impact_group": group,
                    "priority": priority,
                    "reason": reason,
                    "evidence": factor.get("evidence", ""),
                    "source_url": factor.get("source_url", ""),
                    "recommendation": factor["recommendation"],
                    "first_step": self._first_step(factor),
                }
            )
        return sorted(
            recommendations,
            key=lambda item: (
                GROUP_ORDER.get(item["impact_group"], 9),
                STATUS_ORDER.get(item["status"], 9),
                item["factor_id"],
            ),
        )

    @staticmethod
    def _first_step(factor: dict) -> str:
        if factor["status"] == "not_evaluable":
            return "Confirmar manualmente con una fuente publica o configurar la integracion requerida."
        if factor["status"] == "partial":
            return "Completar la evidencia visible y enlazarla desde navegacion, producto o pie de pagina."
        return "Publicar una seccion o componente visible y verificable asociado a este factor."
