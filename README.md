# google-reviews-to-js

Convierte las reseñas de Google Maps (JSON generado por un scraper de Google Maps) en un archivo `googleReviews.js` listo para usar en un componente Vue.

## Qué hace

- Lee un archivo JSON con reseñas de Google Maps.
- Ordena por fecha de publicación y se queda con las **30 más recientes** (configurable).
- Genera un módulo JS con la estructura que espera el componente de reseñas.
- Incluye la foto de perfil del autor cuando existe (`avatar`) y asigna un color de avatar (`avatarColor`) tomado de la paleta del sitio, para usarlo junto a la letra inicial cuando no hay foto.

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas (solo librería estándar)

## Uso

1. Guarda el JSON del scraper como `resenas.json` (codificación UTF-8).
2. Ejecuta:

```bash
python generate_reviews.py resenas.json -o src/data/googleReviews.js \
  --rating 4.9 --total-reviews 127 \
  --maps-url "https://www.google.com/maps/search/?api=1&query=Mi+clinica"
```

> En Windows (CMD o PowerShell) escribe el comando en una sola línea, sin las `\`.

### Opciones

| Opción | Descripción | Valor por defecto |
|---|---|---|
| `input` | Archivo JSON con las reseñas (obligatorio) | — |
| `-o`, `--output` | Ruta del archivo JS generado | `googleReviews.js` |
| `--limit` | Máximo de reseñas a incluir | `30` |
| `--rating` | Calificación global del perfil en Google | Promedio de las reseñas incluidas |
| `--total-reviews` | Total de reseñas en Google | Número de reseñas incluidas |
| `--maps-url` | Enlace a tu ficha de Google Maps | Enlace de ejemplo |
| `--title` | Título de la sección | `Lo que dicen nuestros pacientes` |
| `--intro` | Texto introductorio | `Tu experiencia nos ayuda a seguir cuidando cada sonrisa.` |

## Formato de entrada

Una lista JSON donde cada reseña usa estos campos (los que genera el scraper):

| Campo | Se usa para |
|---|---|
| `Name` | `name` |
| `When` | `date` |
| `Rating` | `rating` |
| `Description` | `text` |
| `ProfilePicture` | `avatar` |
| `posted_at_unix_micros` | Ordenar de más reciente a más antigua |

## Formato de salida

```javascript
export const googleReviews = {
  rating: 4.9,
  totalReviews: 127,
  googleMapsUrl: 'https://www.google.com/maps/search/?api=1&query=Mi+clinica',
  title: 'Lo que dicen nuestros pacientes',
  intro: 'Tu experiencia nos ayuda a seguir cuidando cada sonrisa.',

  reviews: [
    {
      id: 1,
      name: 'Fernanda Santos',
      date: 'Hace 3 meses',
      rating: 5,
      text: 'Súper recomendable! Me dio muchísima confianza la doctora, muy amable y realista.',
      url: 'https://www.google.com/maps/search/?api=1&query=Mi+clinica',
      avatar: 'https://lh3.googleusercontent.com/...',
      avatarColor: '#7cc6e0',
    },
    // ...
  ],
};
```

Si la reseña no tiene foto de perfil, `avatar` es `null`.

## Componente Vue

El componente de reseñas debe mostrar `review.avatar` cuando exista y, si no (o si la imagen falla al cargar), la inicial del nombre sobre `review.avatarColor`.

```vue
<div class="avatar" :style="{ backgroundColor: review.avatarColor }" aria-hidden="true">
  <img
    v-if="review.avatar && !failedAvatars[review.id]"
    :src="review.avatar"
    alt=""
    loading="lazy"
    referrerpolicy="no-referrer"
    @error="failedAvatars[review.id] = true"
  />
  <span v-else>{{ review.name.charAt(0).toUpperCase() }}</span>
</div>
```

```javascript
import { reactive } from 'vue';
const failedAvatars = reactive({});
```

```css
.avatar { overflow: hidden; }
.avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
```

## Notas

- El color de avatar se elige de la paleta según el nombre (hash), así que es estable: no cambia cada vez que regeneras el archivo. Puedes editar la lista `PALETTE` en el script.
- El campo `url` de cada reseña es siempre el valor de `--maps-url`, es decir, la página de reseñas de tu lugar en Google Maps. No se usa el perfil del autor (`author_url`), para que quien haga clic en "Leer reseña completa" llegue a tu ficha y no al perfil de otra persona.
- El JSON original contiene nombres y fotos de personas reales. Considera no subirlo al repositorio (añádelo a `.gitignore`) y versionar solo el `googleReviews.js` generado.

## Estructura sugerida

```
google-reviews-to-js/
├── generate_reviews.py
├── README.md
├── .gitignore        # resenas.json
└── resenas.json      # no se versiona
```