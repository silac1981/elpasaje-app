# EVALUACIÓN DE HOSTING — ¿Vercel sirve para El Pasaje?
### 24/09/2026 · Disparado por: "¿no se puede usar Vercel?"

---

## 1. Lo que hoy corre en 3 lugares distintos

| Pieza | Qué es | Dónde vive hoy | Requiere |
|---|---|---|---|
| **Hub + 10 páginas de línea** (`index.html`, `oasis-animal.html`, `magnitud19.html`, etc.) | HTML/CSS/JS estático, sin backend propio. Lee `exports/*.json` con `fetch()` en el navegador. | GitHub Pages (`silac1981.github.io/elpasaje-app`) | Solo servir archivos. Nada de servidor. |
| **App interna** (`main.py` + `modules/*.py`) — login admin/Fer/socios, panel_socio, dashboard_admin, Mike, etc. | App Python con **Streamlit**, que mantiene una conexión websocket abierta todo el tiempo que el usuario tiene la pestaña abierta (así refresca la UI sin recargar la página). | Streamlit Community Cloud (`elpasaje.streamlit.app`) | Un proceso Python corriendo 24/7, con estado de sesión por usuario. |
| **Base de datos** | PostgreSQL | Supabase (org "El Pasaje 3D Studio") | Un servidor de base de datos persistente. |

Son 3 necesidades técnicas distintas, y por eso hoy están en 3 lugares distintos. La pregunta de Vercel aplica distinto a cada una.

---

## 2. ¿Qué es Vercel, en una línea?

Una plataforma para **sitios estáticos y funciones serverless** (código que se ejecuta por segundos y se apaga — no procesos que quedan corriendo). Es excelente para lo primero de la tabla de arriba. Es una mala opción para el segundo.

### Por qué NO sirve para la app interna (Streamlit)
- Streamlit necesita un **proceso persistente con WebSocket** para que la interfaz reaccione sin recargar la página (clic en un botón → la UI cambia al toque). Las funciones serverless de Vercel se apagan a los segundos — no hay "proceso" que quede escuchando.
- No es un límite de configuración, es la arquitectura misma de Streamlit. No existe una forma soportada de correr Streamlit en Vercel — llevarlo ahí significaría **reescribir toda la app interna** en otra tecnología (por ejemplo Next.js + una API propia), no "mudarla".
- Esto no es un problema exclusivo de Vercel: pasa lo mismo con Netlify o cualquier hosting puramente serverless/estático.

### Dónde SÍ tendría sentido Vercel hoy
- El **hub + catálogos públicos** — hoy en GitHub Pages, que ya funciona bien y no tiene el problema del login que sí tiene la app de Streamlit. Mudarlo a Vercel no arreglaría nada roto, pero sería una opción válida si en algún momento se quiere:
  - Dominio propio con SSL automático más simple que GitHub Pages
  - Preview deployments por rama/PR (útil si en algún momento se versiona el diseño de las páginas)
  - Analytics de tráfico integrado
  - Redirects/rewrites más flexibles (ej. URLs lindas sin `.html`, que hoy ya funcionan solo porque GitHub Pages corre Jekyll por default — no hay `.nojekyll` en el repo)

No es urgente ni resuelve el bloqueo actual de Agustina. Es una mejora de "nice to have" para cuando el foco no sea apagar incendios.

---

## 3. El problema real de Agustina no es de plataforma

El bloqueo que encontramos (Streamlit Cloud pide login de la plataforma antes de llegar al login interno) es un **ajuste de configuración dentro del mismo Streamlit Cloud** (Settings → Sharing de la app), no algo que Vercel resuelva. Cambiar de hosting para esquivar un checkbox mal puesto sería usar una bazuca para matar una mosca — y de paso, te obligaría a reescribir meses de trabajo (login, roles, 9 tabs del panel de socio, Mike, presupuestador, etc.).

**Pasos concretos para revisarlo ahora:**
1. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta que administra la app.
2. Buscar la app "elpasaje" en el listado y abrir su menú (⋮ o ícono de engranaje) → **Settings**.
3. Ir a la pestaña **Sharing** (o "General", según la versión de la UI).
4. Ahí debería haber una opción del tipo "This app is public" vs. una lista de viewers autorizados por mail. Si está en modo restringido, ponerla en **público**, o agregar `oasisanimal@elpasaje.com` a la lista de viewers permitidos.
5. Guardar y volver a probar `elpasaje.streamlit.app` en una ventana nueva (o incógnito, para no arrastrar una sesión ya logueada tuya).

Si la UI no coincide exactamente con esto (Streamlit cambia el dashboard de vez en cuando), contame qué ves y seguimos desde ahí.

---

## 4. Alternativas reales si algún día se quiere dejar Streamlit Cloud

Esto **no es necesario hoy** — es solo referencia si en el futuro el auth-gate de Streamlit Cloud sigue dando problemas o se quiere más control (dominio propio, sin límites del free tier, etc.). Todas estas sí soportan procesos persistentes como Streamlit:

| Opción | Qué ofrece |
|---|---|
| **Render** | Deploy directo desde GitHub, plan gratis con sleep tras inactividad (como Streamlit Cloud), fácil de migrar sin tocar código |
| **Railway** | Similar a Render, buena experiencia para apps chicas/medianas, sin capa de auth-gate propia |
| **Fly.io** | Más control (regiones, recursos), un poco más de curva de aprendizaje |
| Un VPS chico (ej. DigitalOcean) | Control total, pero hay que mantenerlo vos (updates, uptime) |

Ninguna de estas requiere reescribir `main.py`/`modules/` — es la misma app Streamlit, solo cambia dónde corre.

---

## 5. Sobre "el proyecto de ML" (ProyectoML-TalentoTech)

Miré la carpeta antes de escribir esto para no comparar con algo que no existe. Hoy `ProyectoML-TalentoTech` es un TP de la cursada de Talento Tech — notebooks, datasets, sin repo git inicializado todavía (está anotado como pendiente en `PENDIENTES.md`) y sin ninguna app propia desplegada en Vercel. El único rastro de "Vercel" que encontré ahí es un HTML guardado de la consigna de entrega (`ML - Consigna - Entrega final.html`), que parece ser una página de la plataforma de la cursada, no algo que vos hayas deployado.

Si te referías a otro proyecto con Vercel real (por ejemplo algo del portfolio que querés armar), contame cuál es y lo reviso para comparar de verdad — con esto no hay nada concreto todavía para reutilizar entre proyectos.

---

## 6. Resumen

- **La web pública** ya está bien donde está (GitHub Pages). Vercel es una opción válida a futuro, no una urgencia.
- **La app interna no puede vivir en Vercel** sin reescribirla — no es una migración, es un proyecto nuevo.
- **El bloqueo de Agustina se arregla en 2 minutos** en la configuración de Sharing de Streamlit Cloud (paso a paso arriba).
- Si el objetivo de fondo es "quiero dejar de depender de Streamlit Cloud", la conversación correcta es Render/Railway/Fly — no Vercel.

---

*El Pasaje 3D Studio · Evaluación de hosting · 24/09/2026*
