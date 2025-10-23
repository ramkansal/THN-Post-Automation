INDEX_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{title}}</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-neutral-950 text-neutral-100">
  <div class="max-w-4xl mx-auto p-6">
    <h1 class="text-3xl font-semibold mb-6">{{title}}</h1>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="mb-4">
          {% for m in messages %}
            <div class="rounded-xl bg-amber-900/30 border border-amber-700 px-4 py-3 text-amber-200">{{m}}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <form method="post" action="{{ url_for('run') }}" class="grid grid-cols-1 gap-5 bg-neutral-900/60 p-5 rounded-2xl border border-neutral-800">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label class="block">
          <span class="text-sm text-neutral-300">Feed URL</span>
          <input name="feed" type="url" value="{{feed}}" class="mt-1 w-full rounded-xl bg-neutral-800 border border-neutral-700 p-3" required>
        </label>

        <label class="block">
          <span class="text-sm text-neutral-300">Output Root</span>
          <input name="out_root" type="text" value="{{out_root}}" class="mt-1 w-full rounded-xl bg-neutral-800 border border-neutral-700 p-3" required>
        </label>

        <label class="block">
          <span class="text-sm text-neutral-300">Target Date (IST)</span>
          <input name="date" type="date" value="{{today}}" class="mt-1 w-full rounded-xl bg-neutral-800 border border-neutral-700 p-3" required>
        </label>

        <label class="block">
          <span class="text-sm text-neutral-300">Max Items</span>
          <input name="max_items" type="number" min="1" placeholder="(optional)" class="mt-1 w-full rounded-xl bg-neutral-800 border border-neutral-700 p-3">
        </label>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <label class="flex items-center gap-3">
          <input name="overwrite" type="checkbox" class="h-5 w-5 rounded" />
          <span>Overwrite existing files</span>
        </label>
      </div>

      <div class="flex items-center gap-3">
        <button class="px-5 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 transition font-semibold">Run</button>
        <a href="{{ url_for('browse_root') }}" class="px-5 py-3 rounded-2xl bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 transition">Open Output</a>
      </div>

      <p class="text-xs text-neutral-400">
        Summaries are extracted from RSS feed descriptions. Timezone is IST.
      </p>
    </form>
  </div>
</body>
</html>
"""

RESULTS_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{title}} — Results</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-neutral-950 text-neutral-100">
  <div class="max-w-5xl mx-auto p-6">
    <a href="{{ url_for('index') }}" class="text-sm text-neutral-300 hover:underline">← Back</a>
    <h1 class="text-3xl font-semibold mt-3 mb-2">{{title}} — {{target_date}}</h1>
    <p class="text-neutral-400 mb-6">Saved to: <code class="text-neutral-300">{{root}}</code></p>

    {% if count == 0 %}
      <div class="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <p>No items for the selected date.</p>
      </div>
    {% else %}
      <div class="space-y-4">
        {% for it in items %}
          <div class="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
            <div class="flex justify-between items-start gap-4">
              <div>
                <h2 class="text-lg font-semibold">{{ it.title }}</h2>
                <a class="text-sky-400 hover:underline break-all" href="{{ it.link }}" target="_blank">{{ it.link }}</a>
              </div>
              {% if it.image_saved %}
                <span class="text-xs px-2 py-1 rounded-full bg-emerald-800/40 border border-emerald-700">image saved</span>
              {% else %}
                <span class="text-xs px-2 py-1 rounded-full bg-neutral-800 border border-neutral-700">no image</span>
              {% endif %}
            </div>
            <div class="mt-3 flex flex-wrap gap-2">
              {% for kind, relpath in it.paths.items() %}
                <a class="px-3 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-sm"
                   href="{{ url_for('serve_file', relpath=relpath) }}" target="_blank">{{ kind }} file</a>
              {% endfor %}
            </div>
            {% if it.errors %}
              <div class="mt-3 text-sm text-amber-300">
                <ul class="list-disc pl-5">
                  {% for e in it.errors %}
                    <li>{{ e }}</li>
                  {% endfor %}
                </ul>
              </div>
            {% endif %}
          </div>
        {% endfor %}
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

BROWSER_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{title}} — Output</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-neutral-950 text-neutral-100">
  <div class="max-w-5xl mx-auto p-6">
    <a href="{{ url_for('index') }}" class="text-sm text-neutral-300 hover:underline">← Back</a>
    <h1 class="text-3xl font-semibold mt-3 mb-4">{{title}} — Output</h1>
    <p class="text-neutral-400 mb-6">Root: <code class="text-neutral-300">{{root}}</code></p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      {% for entry in entries %}
        <a class="block rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 hover:bg-neutral-800 transition"
           href="{{ entry.href }}">
          <div class="text-lg font-medium">{{ entry.name }}</div>
          <div class="text-xs text-neutral-400 mt-1">{{ entry.type }}</div>
        </a>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""
