# PEC Auditor

Demo académica en Streamlit para diagnosticar factores críticos de éxito (FCE) públicamente observables en un e-commerce. La herramienta no entrena modelos, no calcula AUC ni usa SHAP. Su resultado se explica con evidencia pública y confirmaciones manuales.

## Alcance

El catálogo operativo está en `factor_catalog.json` y contiene exactamente 30 FCE: 10 tecnológicos, 10 organizacionales y de proceso, 4 ambientales visibles y 6 de consumidor. Cada FCE usa uno de estos estados:

- `present`: 1 punto.
- `partial`: 0.5 puntos.
- `absent`: 0 puntos.
- `not_evaluable`: 0 puntos hasta recibir una confirmación manual.

El Índice PEC es la suma simple de los 30 FCE. Sus rangos son: 25-30 Muy alto, 19-<25 Alto, 12-<19 Moderado, 6-<12 Bajo y 0-<6 Inicial.

La matriz histórica `toec_matrix.json` se conserva como referencia académica del marco TOEC amplio. No participa en el puntaje operativo.

## Instalación y ejecución

Requiere Python 3.10 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Después abra `http://localhost:8501`. Si desea personalizar límites, copie `.env.example` como `.env` y configure las variables en su entorno.

## Funcionamiento

1. Ingrese una URL pública `http` o `https`.
2. El sistema bloquea localhost, dominios `.local`, IP privadas, reservadas y redirecciones fuera del dominio inicial.
3. Se recorren como máximo 10 páginas HTML públicas del mismo origen, con un timeout de 20 segundos por página.
4. Se detecta evidencia por reglas explícitas, se calcula el PEC y se generan recomendaciones para FCE parciales, ausentes o no evaluables.
5. En **Factores y evidencia** puede confirmar manualmente cada FCE. La corrección recalcula el índice y conserva la evidencia automática.
6. El historial y feedback se guardan en `data/pec_auditor.db`; cada auditoría puede descargarse como PDF.

No se inicia sesión, no se solicitan datos personales y no se intenta evadir captchas, robots o controles del sitio. La métrica de rendimiento no se simula: sin una medición externa queda como **No evaluable** y debe confirmarse manualmente.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas verifican puntaje, rangos de madurez, correcciones, SQLite y validación de URL. Para una comprobación manual, pruebe una URL pública, una URL inválida, `http://localhost:8501`, una IP privada y una tienda autorizada o de demostración.
