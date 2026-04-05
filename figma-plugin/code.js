// Designer AI — Figma Plugin (code.js)
// Popula templates de carrossel a partir do output do Designer AI.
//
// Convenção de layers no template Figma:
//   "texto 1", "texto 2", ... "texto N"  → camadas de texto
//   "imagem 1", "imagem 2", ...          → camadas de imagem (rectangle fills)
//   "Perfil"                             → @handle
//   "Nome"                               → nome da marca
//   "Foto Perfil"                        → avatar/logo

figma.showUI(__html__, { width: 400, height: 640, themeColors: true });

// ─── Mensagens da UI ───────────────────────────────────────────
figma.ui.onmessage = async (msg) => {
  try {
    switch (msg.type) {
      case 'apply-all':
        await applyAll(msg.texts, msg.colors, msg.profile, msg.images);
        break;
      case 'apply-texts':
        await applyTexts(msg.texts);
        break;
      case 'apply-colors':
        applyColors(msg.colors);
        break;
      case 'apply-profile':
        await applyProfile(msg.profile);
        break;
      case 'apply-images':
        await applyImages(msg.images);
        break;
      case 'extract-colors':
        extractColors();
        break;
      case 'export-zip':
        await exportZip(msg.name);
        break;
    }
  } catch (err) {
    sendStatus(`Erro: ${err.message}`, false);
  }
};

// ─── Aplicar tudo ──────────────────────────────────────────────
async function applyAll(texts, colors, profile, images) {
  const selection = getSelection();
  if (!selection) return;

  let applied = 0;
  applied += await doApplyTexts(selection, texts);
  applied += doApplyColors(selection, colors);
  applied += await doApplyProfile(selection, profile);
  if (images && images.length > 0) {
    applied += await doApplyImages(selection, images);
  }

  sendStatus(`✅ Aplicado! ${applied} layers atualizados.`, true);
}

// ─── Textos ────────────────────────────────────────────────────
async function applyTexts(texts) {
  const selection = getSelection();
  if (!selection) return;

  const count = await doApplyTexts(selection, texts);
  sendStatus(`✅ ${count} textos aplicados.`, true);
}

async function doApplyTexts(root, texts) {
  let count = 0;

  for (const item of texts) {
    const layerName = item.index != null ? `texto ${item.index}` : null;
    if (!layerName) continue;

    const nodes = findByName(root, layerName);
    for (const node of nodes) {
      if (node.type === 'TEXT') {
        await loadAndSetText(node, item.content);
        count++;
      }
    }
  }

  return count;
}

async function loadAndSetText(node, text) {
  // Carrega todas as fontes usadas no nó de texto
  const fonts = node.getRangeAllFontNames(0, node.characters.length);
  for (const font of fonts) {
    await figma.loadFontAsync(font);
  }
  node.characters = text;
}

// ─── Cores ─────────────────────────────────────────────────────
function applyColors(colors) {
  const selection = getSelection();
  if (!selection) return;

  const count = doApplyColors(selection, colors);
  sendStatus(`✅ ${count} cores aplicadas.`, true);
}

function doApplyColors(root, hexColors) {
  if (!hexColors || hexColors.length < 3) return 0;

  const rgbColors = hexColors.map(hexToRgb);
  let count = 0;

  // Mapeamento: cor 1 → fundos claros, cor 2 → accent/destaque, cor 3 → fundos escuros
  // Procura layers com nomes específicos de cor ou aplica por convenção
  const colorMap = [
    { names: ['fundo claro', 'bg-light', 'cor 1', 'light-bg'], color: rgbColors[0] },
    { names: ['accent', 'destaque', 'cor 2', 'primary'], color: rgbColors[1] },
    { names: ['fundo escuro', 'bg-dark', 'cor 3', 'dark-bg'], color: rgbColors[2] },
  ];

  for (const mapping of colorMap) {
    for (const name of mapping.names) {
      const nodes = findByName(root, name);
      for (const node of nodes) {
        applyColorToNode(node, mapping.color);
        count++;
      }
    }
  }

  // Se não encontrou layers nomeados, aplica por posição nos slides
  if (count === 0) {
    count = applyColorsByStructure(root, rgbColors);
  }

  return count;
}

function applyColorToNode(node, rgb) {
  if ('fills' in node) {
    const fills = JSON.parse(JSON.stringify(node.fills));
    if (fills.length > 0 && fills[0].type === 'SOLID') {
      fills[0].color = rgb;
      node.fills = fills;
    } else {
      node.fills = [{ type: 'SOLID', color: rgb }];
    }
  }
}

function applyColorsByStructure(root, rgbColors) {
  // Heurística: aplica cor 2 (accent) em textos "texto 1" (tag),
  // e nas camadas cujo nome contenha "destaque" ou "accent"
  let count = 0;
  const allText = findAllTextNodes(root);

  for (const node of allText) {
    const name = node.name.toLowerCase();
    if (name === 'texto 1' || name.includes('tag') || name.includes('chapéu')) {
      // Aplica accent no texto do chapéu/tag
      applyTextColor(node, rgbColors[1]);
      count++;
    }
  }

  return count;
}

function applyTextColor(node, rgb) {
  if (node.type === 'TEXT') {
    const fills = JSON.parse(JSON.stringify(node.fills));
    if (fills.length > 0 && fills[0].type === 'SOLID') {
      fills[0].color = rgb;
      node.fills = fills;
    }
  }
}

// ─── Perfil ────────────────────────────────────────────────────
async function applyProfile(profile) {
  const selection = getSelection();
  if (!selection) return;

  const count = await doApplyProfile(selection, profile);
  sendStatus(`✅ Perfil atualizado (${count} layers).`, true);
}

async function doApplyProfile(root, profile) {
  let count = 0;

  if (profile.handle) {
    const handleNodes = findByName(root, 'Perfil');
    for (const node of handleNodes) {
      if (node.type === 'TEXT') {
        await loadAndSetText(node, profile.handle);
        count++;
      }
    }
  }

  if (profile.name) {
    const nameNodes = findByName(root, 'Nome');
    for (const node of nameNodes) {
      if (node.type === 'TEXT') {
        await loadAndSetText(node, profile.name);
        count++;
      }
    }
  }

  return count;
}

// ─── Imagens ───────────────────────────────────────────────────
async function applyImages(images) {
  const selection = getSelection();
  if (!selection) return;

  const count = await doApplyImages(selection, images);
  sendStatus(`✅ ${count} imagens aplicadas.`, true);
}

async function doApplyImages(root, images) {
  let count = 0;

  for (let i = 0; i < images.length; i++) {
    const layerName = `imagem ${i + 1}`;
    const nodes = findByName(root, layerName);

    if (nodes.length === 0) continue;

    // Converte base64 data URL para Uint8Array
    const base64 = images[i].split(',')[1];
    const bytes = figma.base64Decode(base64);
    const imageHash = figma.createImage(bytes).hash;

    for (const node of nodes) {
      if ('fills' in node) {
        node.fills = [{
          type: 'IMAGE',
          scaleMode: 'FILL',
          imageHash: imageHash,
        }];
        count++;
      }
    }
  }

  return count;
}

// ─── Extrair Cores do Frame ────────────────────────────────────
function extractColors() {
  const selection = getSelection();
  if (!selection) return;

  const colors = [];
  const seen = new Set();

  function walk(node) {
    if ('fills' in node && node.fills && node.fills.length > 0) {
      for (const fill of node.fills) {
        if (fill.type === 'SOLID' && fill.visible !== false) {
          const hex = rgbToHex(fill.color);
          if (!seen.has(hex)) {
            seen.add(hex);
            colors.push(hex);
          }
        }
      }
    }
    if ('children' in node) {
      for (const child of node.children) {
        walk(child);
      }
    }
  }

  walk(selection);

  // Envia as cores mais frequentes de volta para a UI
  figma.ui.postMessage({
    type: 'extracted-colors',
    colors: colors.slice(0, 6),
  });
}

// ─── Exportar ZIP ──────────────────────────────────────────────
async function exportZip(name) {
  const selection = getSelection();
  if (!selection) return;

  // Exporta cada filho direto do frame selecionado como PNG
  const children = 'children' in selection ? selection.children : [selection];
  const baseName = name || 'carrossel';
  let exported = 0;

  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    try {
      const bytes = await child.exportAsync({
        format: 'PNG',
        constraint: { type: 'SCALE', value: 2 },
      });
      // Renomeia o frame para manter a numeração
      child.name = `${baseName}_${i + 1}`;
      exported++;
    } catch (e) {
      // Ignora nodes que não podem ser exportados
    }
  }

  sendStatus(`✅ ${exported} slides prontos para exportar. Use File → Export.`, true);
}

// ─── Helpers ───────────────────────────────────────────────────

/** Obtém a seleção atual no Figma. */
function getSelection() {
  const sel = figma.currentPage.selection;
  if (!sel || sel.length === 0) {
    sendStatus('⚠️ Selecione o frame do carrossel antes de aplicar.', false);
    return null;
  }
  return sel[0];
}

/** Busca recursiva por layers com nome exato (case-insensitive). */
function findByName(root, name) {
  const results = [];
  const target = name.toLowerCase();

  function walk(node) {
    if (node.name && node.name.toLowerCase() === target) {
      results.push(node);
    }
    if ('children' in node) {
      for (const child of node.children) {
        walk(child);
      }
    }
  }

  walk(root);
  return results;
}

/** Coleta todos os nós de texto recursivamente. */
function findAllTextNodes(root) {
  const results = [];

  function walk(node) {
    if (node.type === 'TEXT') results.push(node);
    if ('children' in node) {
      for (const child of node.children) {
        walk(child);
      }
    }
  }

  walk(root);
  return results;
}

/** Converte hex (#RRGGBB) para {r, g, b} normalizado (0-1). */
function hexToRgb(hex) {
  const h = hex.replace('#', '');
  return {
    r: parseInt(h.substring(0, 2), 16) / 255,
    g: parseInt(h.substring(2, 4), 16) / 255,
    b: parseInt(h.substring(4, 6), 16) / 255,
  };
}

/** Converte {r, g, b} normalizado (0-1) para hex (#RRGGBB). */
function rgbToHex(rgb) {
  const r = Math.round(rgb.r * 255).toString(16).padStart(2, '0');
  const g = Math.round(rgb.g * 255).toString(16).padStart(2, '0');
  const b = Math.round(rgb.b * 255).toString(16).padStart(2, '0');
  return `#${r}${g}${b}`.toUpperCase();
}

/** Envia mensagem de status de volta para a UI. */
function sendStatus(message, success) {
  figma.ui.postMessage({ type: 'status', message: message, success: success });
}
