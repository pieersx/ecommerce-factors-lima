# Informe del sistema EcomScore

## 1. Nombre del sistema

El sistema desarrollado se denomina **EcomScore**.

EcomScore es una aplicación web académica orientada a evaluar la preparación observable de sitios e-commerce mediante una auditoría pública basada en factores críticos de éxito. El sistema no mide ventas, rentabilidad ni éxito financiero; su objetivo es revisar qué tan completo, verificable y confiable es el canal e-commerce desde evidencia disponible públicamente.

## 2. Propósito del sistema

El propósito de EcomScore es ofrecer una herramienta de diagnóstico para tiendas e-commerce, especialmente en el contexto de Lima Metropolitana, que permita:

- Validar si una URL corresponde realmente a un sitio e-commerce.
- Explorar hasta 15 páginas públicas del mismo dominio.
- Evaluar 30 factores críticos de éxito observables.
- Calcular un puntaje de preparación e-commerce sobre 30 puntos.
- Clasificar el resultado en niveles: Inicial, Bajo, Moderado, Alto y Muy alto.
- Mostrar evidencia trazable por cada factor.
- Estimar la confianza del diagnóstico.
- Priorizar brechas y recomendaciones.
- Generar reportes PDF completos y reportes PDF de brechas.
- Guardar auditorías en una base de datos SQLite local.

## 3. Aporte de investigación

El aporte principal es el **Modelo de Evaluación EcomScore**, una operacionalización de factores críticos de éxito para evaluar preparación e-commerce desde evidencia pública.

El modelo toma como base una revisión académica sobre factores de desempeño en e-commerce y adapta dichos factores a una auditoría observable, reproducible y no invasiva. En lugar de exigir información interna de la empresa, el sistema se limita a evidencia pública disponible en la web.

El aporte metodológico se resume en:

- Selección de 30 FCE núcleo observables públicamente.
- Validación previa para evitar auditar sitios que no son e-commerce.
- Puntaje trazable por factor: presente, parcial, ausente o no evaluable.
- Evaluación de confianza para advertir limitaciones de cobertura o evidencia.
- Recomendaciones priorizadas por impacto.
- Separación entre reglas trazables e IA opcional.

## 4. Artefacto desarrollado

El artefacto es la **Aplicación Web EcomScore**, desarrollada con Python y Streamlit.

La aplicación permite ingresar una URL pública, ejecutar una auditoría automática, revisar los resultados en distintas pestañas, corregir manualmente factores cuando sea necesario, y exportar reportes en PDF.

La interfaz está organizada en seis secciones:

- **Nueva auditoría:** ingreso de URL y ejecución del diagnóstico.
- **Resumen PEC:** puntaje EcomScore, nivel, confianza, distribución de factores y puntaje por dimensión.
- **Factores y evidencia:** revisión detallada de los 30 FCE, filtros y corrección manual.
- **Brechas y recomendaciones:** recomendaciones priorizadas, tabla filtrable y PDF de brechas.
- **Historial:** auditorías guardadas en SQLite.
- **Sobre el proyecto:** explicación académica, objetivo y fuente base de los FCE.

## 5. Arquitectura general

EcomScore usa una arquitectura modular basada en agentes. Cada agente cumple una responsabilidad específica dentro del flujo de auditoría.

El flujo general es:

1. El usuario ingresa una URL.
2. El sistema valida que sea una URL pública segura.
3. El crawler explora hasta 15 páginas públicas del mismo dominio.
4. Se verifica si el sitio tiene señales mínimas de e-commerce.
5. Se identifican los 30 factores críticos de éxito.
6. Se calcula el puntaje EcomScore.
7. Se estima la confianza del resultado.
8. Se generan recomendaciones priorizadas.
9. Opcionalmente, una revisión IA resume riesgos metodológicos.
10. Se guarda la auditoría en SQLite.
11. Se muestran resultados y se habilitan reportes PDF.

## 6. Agentes del sistema

### 6.1 URLAcquisitionAgent

Archivo: `agents/url_acquisition.py`

Este agente valida la URL ingresada por el usuario antes de cualquier exploración.

Funciones principales:

- Acepta solo URLs con esquema `http` o `https`.
- Rechaza URLs con credenciales.
- Bloquea `localhost`, dominios `.local` y redes privadas.
- Resuelve DNS y comprueba que el destino sea público.
- Normaliza la URL para el resto del flujo.

Este agente reduce riesgos de seguridad y evita que la app sea usada para consultar recursos internos o privados.

### 6.2 WebExtractionAgent

Archivo: `agents/web_extraction.py`

Este agente actúa como crawler HTTP acotado.

Funciones principales:

- Explora hasta 15 páginas públicas del mismo dominio.
- Sigue redirecciones de forma controlada.
- Bloquea redirecciones fuera del dominio original.
- Extrae texto, HTML, enlaces, metadatos, imágenes y señales básicas de estructura.
- Detecta activos de marca como nombre del sitio, dominio, logo o imagen pública.
- Registra advertencias cuando una página no puede revisarse.

La exploración no inicia sesión, no realiza compras y no recopila datos privados.

### 6.3 EcommerceQualificationAgent

Archivo: `agents/ecommerce_qualification.py`

Este agente determina si la URL presenta evidencia suficiente para ser tratada como e-commerce.

Señales evaluadas:

- Catálogo o listado de productos.
- Precio visible.
- Carrito o checkout.
- Medios de pago.
- Ficha o detalle de producto.
- Condiciones de compra, envío o devolución.

Estados posibles:

- **qualified:** el sitio califica como e-commerce.
- **weak:** tiene señales débiles y debe interpretarse con cautela.
- **rejected:** no presenta evidencia suficiente de tienda e-commerce.

Si un sitio no califica, EcomScore no calcula el índice para evitar resultados engañosos.

### 6.4 FactorIdentificationAgent

Archivo: `agents/factor_identification.py`

Este agente identifica evidencia para los 30 FCE del catálogo operativo.

Cada factor puede quedar en uno de cuatro estados:

- **Presente:** existe evidencia pública suficiente.
- **Parcial:** existe evidencia incompleta.
- **Ausente:** no se encontró evidencia.
- **No evaluable:** requiere una integración o revisión externa.

El agente usa reglas trazables basadas en patrones de texto, HTML, enlaces y metadatos. Para rendimiento de carga puede usar Google PageSpeed Insights si existe una clave API configurada; si no existe, el factor queda como no evaluable.

### 6.5 ScoringEngine

Archivo: `agents/scoring_engine.py`

Este agente calcula el puntaje EcomScore.

Puntaje por estado:

- Presente: 1 punto.
- Parcial: 0.5 puntos.
- Ausente: 0 puntos.
- No evaluable: 0 puntos.

Rangos de clasificación:

- 25 a 30: Muy alto.
- 19 a 24.5: Alto.
- 12 a 18.5: Moderado.
- 6 a 11.5: Bajo.
- 0 a 5.5: Inicial.

También calcula puntajes por dimensión para mostrar el desempeño relativo del sitio auditado.

### 6.6 ConfidenceAssessmentAgent

Archivo: `agents/confidence_assessment.py`

Este agente estima la confiabilidad del resultado.

Considera:

- Número de páginas revisadas.
- Diversidad de rutas exploradas.
- Cantidad de señales e-commerce.
- Factores no evaluables.
- Advertencias del crawler.

El resultado se expresa como:

- `confidence_score`: valor de 0 a 100.
- `confidence_label`: Alta, Media o Baja.
- `confidence_reasons`: razones legibles para el usuario.

Esto evita interpretar del mismo modo una auditoría con 15 páginas revisadas y otra con una sola página.

### 6.7 RecommendationAgent

Archivo: `agents/recommendations.py`

Este agente genera recomendaciones a partir de factores ausentes, parciales o no evaluables.

Agrupa recomendaciones por impacto:

- Compra.
- Confianza.
- Operación.
- Experiencia.
- Otros.

Cada recomendación incluye:

- FCE relacionado.
- Estado.
- Prioridad.
- Razón.
- Evidencia encontrada o no encontrada.
- Primer paso sugerido.

### 6.8 AIReviewAgent

Archivo: `agents/ai_review.py`

Este agente es opcional y solo funciona si existe `OPENAI_API_KEY`.

Su función no es recalcular el puntaje ni reemplazar las reglas. Actúa como revisor metodológico auxiliar para resumir riesgos de error, falsos positivos, falsos negativos o baja cobertura.

Si no hay clave API, el sistema sigue funcionando completamente con reglas trazables.

### 6.9 Agentes complementarios

El proyecto también conserva módulos auxiliares:

- `GapPrioritizationAgent`: priorización simple de brechas.
- `MaturityClassifier`: adaptador de clasificación del puntaje.
- `EvaluationEngine`: estructura base para evaluación de factores.
- `SHAPExplainer`: módulo experimental para explicabilidad.

Algunos de estos módulos son complementarios o heredados, pero la lógica principal actual se concentra en los agentes descritos anteriormente.

## 7. Catálogo de factores

Archivo: `factor_catalog.json`

El catálogo contiene los 30 FCE operativos evaluados por EcomScore.

Cada factor incluye:

- ID.
- Nombre.
- Dimensión.
- Detector asociado.
- Recomendación base.

Las dimensiones usadas son:

- Tecnológica.
- Organizacional y proceso.
- Ambiental visible.
- Consumidor.

Estos 30 factores representan una versión observable del marco académico, no la totalidad de factores internos que podría evaluar una empresa con acceso a datos privados.

## 8. Interfaz de usuario

Archivo principal: `app.py`

La interfaz está construida con Streamlit y usa una hoja de estilos personalizada inyectada desde Python.

Componentes destacados:

- Logo EcomScore recortado en `assets/ecomscore-logo.png`.
- Header con explicación breve del sistema.
- Formulario de auditoría de URL.
- Métricas principales: EcomScore, nivel PEC, confianza y cobertura.
- Distribución de los 30 FCE.
- Puntaje por dimensión.
- Guía de interpretación colapsable.
- Filtros por dimensión, estado y búsqueda.
- Corrección manual de factores.
- Tabla de brechas filtrable.
- Descarga de PDF completo y PDF de brechas.
- Historial de auditorías guardadas.

## 9. Persistencia de datos

Archivo: `utils/storage.py`

El sistema usa SQLite local.

Base por defecto:

`data/pec_auditor.db`

Tablas principales:

- `audits`: auditorías generales.
- `factor_results`: resultado por factor.
- `feedback`: tabla heredada para comentarios.

La base guarda:

- URL auditada.
- Fecha de creación.
- Páginas revisadas.
- Estado de calificación e-commerce.
- Evidencia e-commerce.
- Puntaje EcomScore.
- Clasificación.
- Confianza.
- Razones de confianza.
- Activos de marca.
- Revisión IA opcional.
- Advertencias.
- Resultados de los 30 factores.

El sistema incluye migraciones compatibles mediante `ALTER TABLE` para auditorías antiguas.

## 10. Reportes PDF

Archivo: `utils/reporting.py`

EcomScore genera dos tipos de reportes:

### 10.1 Informe PDF completo

Incluye:

- Encabezado con marca auditada.
- URL.
- Puntaje.
- Clasificación.
- Confianza.
- Cobertura.
- Nota metodológica.
- Puntaje por dimensión.
- Tabla completa de factores y evidencia.

### 10.2 PDF de brechas y recomendaciones

Incluye:

- Resumen de brechas críticas.
- Factores por revisar.
- Recomendaciones agrupadas.
- Estado, prioridad, evidencia, razón y primer paso.

Este PDF se enfoca solo en brechas, no en la tabla completa de los 30 factores.

## 11. Evaluación de confianza

La confianza no modifica el puntaje EcomScore, pero acompaña su interpretación.

Ejemplo:

- Un sitio puede obtener 22/30, pero si solo se revisó una página, la confianza será baja.
- Esto evita comparar diagnósticos incompletos con auditorías más completas.

La confianza ayuda a interpretar la solidez del resultado.

## 12. Corrección manual

La pestaña “Factores y evidencia” permite ajustar manualmente factores cuando el usuario encuentra evidencia pública que contradice el hallazgo automático.

Cada corrección conserva:

- Estado confirmado.
- Nota o enlace revisado.
- Nuevo cálculo de puntaje.
- Nueva auditoría guardada en historial.

Esto permite combinar automatización con validación humana.

## 13. Pruebas del sistema

El proyecto incluye pruebas unitarias en la carpeta `tests/`.

Coberturas principales:

- Validación de URLs públicas y bloqueo de destinos privados.
- Rechazo de sitios no e-commerce.
- Aceptación de sitios e-commerce.
- Evaluación de confianza cuando solo se encuentra una página.
- Existencia exacta de 30 factores operativos.
- Extracción de activos de marca.
- Scoring y clasificación.
- Corrección manual.
- Persistencia en SQLite.
- Recomendaciones agrupadas por impacto.

Comandos de verificación:

```bash
python -m compileall app.py agents utils
python -m unittest discover -s tests -v
```

Resultado validado:

- Compilación correcta.
- 15 pruebas unitarias ejecutadas correctamente.

## 14. Validación funcional en navegador

Se realizó una prueba funcional en navegador con:

`http://books.toscrape.com/`

Resultado observado:

- La app cargó correctamente en `http://localhost:8502/`.
- Se mostró el logo y la interfaz EcomScore.
- La auditoría finalizó sin errores.
- El sitio calificó como e-commerce.
- Se generó un puntaje EcomScore.
- Se guardó la auditoría en SQLite.
- Las pestañas principales cargaron correctamente.
- No se observaron errores de consola, Traceback ni KeyError.

## 15. Limitaciones

EcomScore tiene las siguientes limitaciones:

- Solo evalúa evidencia pública visible.
- No accede a paneles administrativos, ventas, costos ni métricas internas.
- No inicia sesión ni simula compras reales.
- El límite de 15 páginas puede dejar fuera evidencia existente en sitios grandes.
- Algunos sitios bloquean crawlers o cargan contenido dinámico con JavaScript.
- El factor de rendimiento depende de PageSpeed Insights si se configura API.
- La IA es opcional y no reemplaza reglas ni evidencia.

## 16. Conclusión

EcomScore es una aplicación funcional para auditar preparación e-commerce desde evidencia pública. Integra validación de URLs, crawling acotado, calificación e-commerce, detección de 30 FCE, scoring, confianza, recomendaciones, reportes PDF e historial local.

Como aporte académico, propone un modelo observable y reproducible para diagnosticar tiendas online sin requerir información privada. Como artefacto, entrega una herramienta web usable que automatiza el diagnóstico y permite revisión manual trazable.

