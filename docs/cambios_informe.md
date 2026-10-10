# Actualización del informe: de 30 a 199 muestras

Guía para actualizar *DM Proyecto 2. Análisis Exploratorio* (versión del 07/09/2026) con la corrida
completa en Kaggle (`proyecto2-ds.ipynb`). Va sección por sección: **qué dice → qué debe decir**.

Leyenda: 🔁 cifra a actualizar · ✏️ afirmación a corregir · ➕ contenido nuevo · 🖼️ figura a
regenerar · ⏳ depende de la próxima corrida (5.7.b) · 🔍 verificar en el notebook.

Las secciones 1 (situación problemática), 2 (problema científico) y 3 (objetivos) no requieren
cambios.

---

## Párrafo introductorio

- 🔁 "30 muestras, 15,934 células anotadas, 15,369 enlaces temporales y 565 linajes" →
  **199 muestras, 133,318 células anotadas, 128,883 enlaces y 4,435 linajes**.

## 4. Descripción de los datos

### 4.1 Origen y estrategia de descarga → *Origen y carga de los datos*

- ✏️ Reescribir. Ya no hay descarga selectiva: el análisis corre en un Notebook de Kaggle con los datos
  de la competencia montados en solo lectura (87.6 GB). `zarr` lee directamente los fragmentos que
  necesita.
- ✏️ En la tabla, el uso del `.zarr` pasa a ser: "metadatos de todas las muestras y volúmenes de una
  submuestra (20 muestras × 3 instantes) para el análisis de intensidad".
- ✏️ Quitar "Esta estrategia produjo un conjunto local de 9.6 MB".

### 4.2 Sobre el tamaño de la muestra

- ✏️ Explicar que la limitación a 30 muestras era de la API (errores 404 y descargas incompletas) y que
  ahora se usan las 199.
- ➕ Agregar una columna "199 muestras" a la tabla 8 vs 30 (sale de la sección 5.11 del notebook):

| Resultado | 8 muestras | 30 muestras | 199 muestras | Lectura |
|---|---|---|---|---|
| Desplazamiento mediano, 6bba vs 44b6 | 1.62 vs 2.33 µm | 1.86 vs 1.82 µm | **1.82 vs 1.72 µm** (p = 0.51) | sin diferencia real |
| Divisiones observadas | 4 | 20 | **151** | ahora se pueden analizar |
| p99 del desplazamiento | 7.37 µm | 8.35 µm | **8.38 µm** | estable |
| Densidad global de anotación | 2.10% | 2.05% | **2.82%** | baja en todos los casos |
| Máximo del desplazamiento | — | 17.97 µm | **60.76 µm** | aparece un salto colectivo (5.7) |

- ➕ Mencionar que la columna de 30 se recalculó en el notebook y reproduce exactamente las cifras del
  informe original, lo que valida que el código es el mismo.

### 4.3 Las tablas analíticas construidas

- 🔁 df_samples **199** × 20 · df_nodes **133,318** × 14 · df_edges **128,883** × **14** (se agregaron
  `src_id`, `dst_id`, `z0_um`, `y0_um`, `x0_um`) · df_linajes **4,435** × 6.

### 4.4 Dimensiones y escala física

- 🔁 Nodos por muestra: media **669.9**, mediana **659**, rango 50 – 1,950.
- ✏️ "Almacenamiento total: 9.6 MB" → "Los datos se leen montados en Kaggle (87.6 GB), sin descarga".

### 4.5 Descripción de las variables

- 🔁 `sample`: 199 niveles.
- ➕ Opcional: agregar fila `src_id, dst_id` (identificador: nodos de origen y destino del enlace).
- 🔁 En el párrafo de cuantización: "Entre los 133,318 nodos…".

### 4.6 Limpieza y preprocesamiento

- ✏️ "Validación de integridad de la descarga": conservarla como antecedente (fue lo que obligó a
  limitar la muestra), aclarando que con los datos montados ese riesgo desaparece.
- 🔁 Validaciones finales: "0 en las **199** muestras"; "1.0 en las **128,883** aristas".
- ➕ Agregar al tratamiento de atípicos la referencia a 5.7 (marcas `posible_error` y `salto_instante`).

## 5. Análisis exploratorio

### 5.1 Estadística descriptiva

- 🔁 Nivel muestra (n = 199):

| Variable | media | desv. | mín | mediana | máx |
|---|---|---|---|---|---|
| n_nodos | 669.9 | 421.4 | 50 | 659.0 | 1,950 |
| n_aristas | 647.7 | 406.3 | 49 | 639.0 | 1,879 |
| n_t_anotados | 95.1 | 11.7 | 40 | 100 | 100 |
| cobertura_temporal | 0.951 | 0.117 | 0.40 | 1.00 | 1.00 |
| nodos_por_t | 6.89 | 4.27 | 1.00 | 6.61 | 20.05 |
| aristas_por_nodo | 0.970 | 0.015 | 0.916 | 0.973 | 0.994 |

- ✏️ "la desviación estándar (486.5) equivale al 91.6% de su media (531.1)" → **421.4 equivale al 63%
  de su media (669.9)**. La dispersión sigue siendo alta, pero la muestra pequeña la exageraba.
- 🔁 Nivel nodo (n = 133,318) y nivel arista (n = 128,883):

| Variable | media | desv. | mín | mediana | máx |
|---|---|---|---|---|---|
| t | 49.74 | 28.05 | 0 | 50.0 | 99 |
| z_um | 50.30 | 27.96 | 0 | 50.38 | 102.38 |
| y_um | 51.18 | 27.60 | 0 | 51.59 | 103.59 |
| x_um | 52.64 | 27.96 | 0 | 52.81 | 103.59 |
| dz_um | −0.415 | 1.753 | −60.125 | 0.000 | 56.875 |
| dy_um | 0.144 | 1.453 | −21.125 | 0.000 | 25.594 |
| dx_um | −0.262 | 1.519 | −17.875 | 0.000 | 9.344 |
| dist_um | 2.130 | 1.793 | 0.000 | 1.817 | 60.758 |

### 5.2 Distribuciones univariadas

- 🖼️ Figura 1: usar la nueva. El desplazamiento está en escala log, y la profundidad tiene un bin por
  plano Z. ✏️ La figura anterior tenía un patrón de barras alternadas que era un artefacto del binning
  (64 planos discretos en 40 bins), no una propiedad de los datos.
- 🔁 Cuantiles: p50 **1.82** · p75 **2.73** · p90 **4.14** · p95 **5.34** · p99 **8.38** · máx **60.76** µm.
- ✏️ "el máximo alcanza 17.97 µm, casi diez veces la mediana" → la cola es continua hasta ~26 µm. Los
  valores de 49 – 61 µm vienen de un único salto colectivo (5.7).
- 🔁 Radio inicial: 8.35 → **8.38 µm**.
- 🔁 Nodos por instante: mediana 4 → **6** (rango 1 – 33).
- 🔍 "Frente a las 4,836–78,644 células estimadas": tomar el rango nuevo de la salida de 5.4, que ahora
  lo imprime.
- ✏️ Profundidad: quitar "aun cuando la muestra visual presenta una atenuación". Con un bin por plano
  la distribución es suave, con pocos centroides en el primer y el último plano y acumulaciones cerca
  de ~5 y ~97 µm (posiblemente núcleos cortados por el borde del volumen).

### 5.3 Variables categóricas

- 🔁 Tabla:

| Variable | Categoría | Frecuencia | % |
|---|---|---|---|
| embryo_id (muestras) | 6bba / 44b6 | 128 / 71 | 64.32 / 35.68 |
| embryo_id (nodos) | 6bba | 113,121 | **84.85** |
| | 44b6 | 20,197 | **15.15** |
| tipo_temporal | intermedio | 124,297 | **93.23** |
| | fin | 4,586 | 3.44 |
| | inicio | 4,435 | 3.33 |
| out_degree | 1 | 128,581 | 96.45 |
| | 0 | 4,586 | 3.44 |
| | **2 (división)** | **151** | **0.11** |
| in_degree | 1 | 128,883 | 96.67 |
| | 0 | 4,435 | 3.33 |

- 🔁 Texto: 92.78% → **93.23%** intermedios; 0.13% → **0.11%** divisiones; inicio/fin 3.55/3.67 →
  **3.33/3.44%**; por embrión 95.4/92.2 → **96.2/92.7%**.
- ➕ El conjunto está desbalanceado: 6bba aporta el 64% de las muestras y el 85% de los nodos.
- 🖼️ Figura 2 y la nueva figura de barras.

### 5.4 Esparcidad de la anotación

- 🔁 Densidad global 2.05% → **2.82%**.
- 🔁 Rango 0.13 – 15.42%, factor 121× → **0.13 – 20.21%, factor 159×**.
- 🔁 Por embrión: 6bba 8.23% (0.93 – 15.42) → **8.98% (0.93 – 20.21)**; 44b6 0.74% (0.13 – 2.90) →
  **0.99% (0.13 – 5.02)**.
- 🔍 Células estimadas por volumen, rango y factor: tomarlos de la salida de 5.4.
- 🖼️ Figura 3: el barplot por muestra ya no es legible con 199. Usar la nueva (boxplot por embrión y
  dispersión coloreada por embrión).

### 5.5 Análisis bivariado

- ✏️ **"No se observa una deriva direccional marcada" es incorrecto.** Ver 5.6.
- 🔁 Cobertura temporal media 91.0% → **95.1%** (mínimo 40%). 🔍 La frase "algunas muestras de 44b6
  abarcan entre 40% y 52%" se puede verificar con `cobertura_temporal_min` en la tabla de 5.5.
- 🔁 Tabla de comparación entre embriones:

| Embrión | Muestras | Nodos | Desplazamiento mediano | p99 | Densidad media |
|---|---|---|---|---|---|
| 6bba | 128 | 113,121 | 1.82 µm | 8.49 µm | 8.98% |
| 44b6 | 71 | 20,197 | 1.72 µm | 7.20 µm | 0.99% |

- ✏️ "difieren por un factor aproximado de once" → **de nueve**.
- ➕ Prueba de Mann-Whitney con la muestra como unidad: desplazamiento p = 0.51 (sin diferencia);
  densidad p ≈ 10⁻²⁸ y nodos por instante p ≈ 10⁻²⁵. Esto refuerza que la diferencia entre embriones
  está en la anotación, no en el movimiento.
- 🖼️ Figura 4 y gráficas temporales nuevas, coloreadas por embrión.

### 5.6 Correlaciones

- 🖼️ Figura 5: usar la nueva, sin la fila y columna en blanco de `dt`. ✏️ El pie de figura decía "a
  nivel de muestra (n = 30)", pero la segunda matriz es a **nivel nodo** (n = 133,318).
- ✏️ **Corregir la interpretación.** "La relación de dist_um con dz/dy/dx es esperable porque la
  distancia se calcula a partir de esos componentes" no explica una correlación con una componente con
  signo: si el movimiento fuera simétrico, sería ≈ 0. El signo negativo indica que los desplazamientos
  grandes van hacia Z y X negativos.
- ➕ Agregar el análisis de deriva:
  - Persiste sin extremos (−0.28) y con Spearman (−0.28).
  - El 66.6% de los pasos en Z son negativos (2:1).
  - Deriva por muestra: 6bba −0.52 ± 0.14 µm/frame en Z (73% de muestras negativas) y −0.36 en X;
    44b6 −0.21 ± 0.18 en Z (70%).
  - Cerca del 30% de las muestras va en sentido contrario, lo que es compatible con flujos de tejido
    que dependen de la región.
- ✏️ Implicación: un costo simétrico sigue siendo viable (0.5 µm/frame ≪ 8.4 µm), pero el enlace debería
  predecir la posición con la deriva local. Acumulada en un linaje mediano, suma ~11 µm.

### 5.7 Valores atípicos

- 🔁 Tabla: Tukey 5.82 → **5.45 µm**; atípicos 611 de 15,369 (3.98%) → **6,060 de 128,883 (4.70%)**;
  máximo 17.97 → **60.76 µm**; 6bba/44b6 4.45/1.83% → **5.17/2.12%**; nodo normal 3.9% → **4.6%**;
  nodo que se divide 42.5% → **54.3%**.
- ✏️ "La proporción de 42.5% se calculó sobre 20 divisiones y tiene alta incertidumbre" → ahora son
  151 divisiones. La serie 62.5% (8) → 42.5% (30) → **54.3% (199)** confirma la asociación.
- ➕ Clasificación de extremos (más allá de q3 + 3·RIC = 8.18 µm): 1,502 aristas, de las cuales 88%
  son saltos sostenidos (la cola real del movimiento) y solo 64 son de ida y vuelta (0.05%, errores
  puntuales sin efecto en los cuantiles).
- ➕ Decisión documentada: conservar los atípicos moderados; marcar `posible_error` y `salto_instante`
  y excluirlos solo al estimar parámetros, sin eliminarlos de la referencia.
- ➕ ⏳ **Salto colectivo** en `6bba_f20478e9`, t = 64 → 65: muchas células saltan juntas ≈ +50 µm en Z.
  Completar con el veredicto de 5.7.b: si se movió la imagen (adquisición, habría que registrar) o solo
  la anotación (error de anotación).

### 5.8 Eventos de división celular

- 🔁 20 divisiones en 15,934 nodos (0.126%, 1:796) → **151 en 133,318 (0.113%, ≈ 1:882)**.
- 🔁 Presentes en 12 de 30 muestras → **87 de 199**.
- 🔁 Reparto: 16 en 6bba (8 muestras) y 4 en 44b6 (4) → **125 en 6bba (66 muestras) y 26 en 44b6 (21)**.
- ➕ Tasa por nodo similar entre embriones: 0.11% y 0.13%.
- ✏️ "La interpretación está limitada por la presencia de solo 20 eventos… sustenta la ampliación de
  la muestra" → la ampliación ya se hizo.
- 🖼️ Figura 6: la leyenda de 30 muestras se reemplaza por una curva por embrión.

### 5.9 Longitud de los linajes

- 🔁 565 → **4,435** linajes.
- 🔁 duracion: media 27.92 → **29.52**, desv. 23.14 → **24.26**, mediana 20 → **21**, máx 100.
- 🔁 n_nodos: media 28.20 → **30.06**, desv. 23.50 → **25.54**, máx 111 → **187**.
- ✏️ "Que el máximo de n_nodos (111) supere…" → 187.
- ➕ El número de linajes coincide exactamente con el de nodos de inicio (4,435): cada linaje tiene una
  sola raíz, lo que valida la construcción del grafo.
- 🖼️ Figura 7.

### 5.10 Inspección visual de la imagen

- ✏️ "se descargó un único instante" → "se leyó".
- ✏️ **La atenuación del 92% no es representativa.** Agregar el análisis de 20 volúmenes × 3 instantes:
  - Atenuación mediana de 13% (44b6) y 35% (6bba), con un rango de −442% a 96%. Hay volúmenes más
    brillantes en el fondo, y uno con el máximo a ~45 µm.
  - 44b6 es ~3 veces más brillante (p99 2,165 vs 710).
  - No hay fotoblanqueo: la señal **aumenta** con el tiempo (+68% y +39% entre t = 0 y t = 99).
- ✏️ Cambia la decisión de preprocesamiento: en lugar de "evaluar una corrección de intensidad en Z",
  **normalizar por cuantiles en cada volumen y en cada instante**.
- ✏️ Quitar "estas mediciones proceden de un solo instante de una sola muestra" (ya no es cierto) o
  convertirlo en la comparación con 5.10.b.

## 6. Hallazgos y conclusiones

- ✏️ 6.1: reemplazar por el resumen de la sección 6.1 del notebook. Los cambios principales: hay
  deriva, la atenuación es variable, los atípicos extremos son pocos y hay un salto colectivo.
- ✏️ 6.2 Limitaciones:
  - "Las 30 muestras proceden de solo dos embriones" → **199 muestras**, mismo problema.
  - "Frecuencia de divisiones: 20 eventos insuficientes" → **151 eventos**; la limitación se reduce
    mucho.
  - "Cobertura del análisis de imagen: un instante de una muestra" → **20 volúmenes en 3 instantes**.
  - ➕ La causa de la deriva (tejido o adquisición) no se puede determinar con estos datos.
  - 🔁 "15,934 nodos y 15,369 aristas" → **133,318 y 128,883**.
- ✏️ 6.3 Próximos pasos:
  - Quitar "Ampliar el análisis a las 199 muestras" (ya está hecho).
  - Radio inicial 8.35 → **8.38 µm**, estimado sin `posible_error` ni `salto_instante`, con
    predicción de posición por deriva local.
  - Reemplazar "validar la normalización por cuantiles y la corrección de atenuación en Z" por
    "normalizar por cuantiles en cada volumen e instante".
  - ⏳ Si 5.7.b confirma un salto de adquisición: agregar registro entre instantes antes del enlace.

## Figuras

🖼️ Todas las figuras deben regenerarse desde la corrida de 199 muestras. Las de las secciones 5.2,
5.3, 5.4, 5.6 y 5.8 además cambiaron de diseño.

## Referencias

- ➕ Opcional: citar Kaggle Notebooks como entorno de ejecución y agregar el link al notebook público y
  al repositorio, que también son entregables.
