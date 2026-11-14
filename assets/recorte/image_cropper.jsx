// Moldura de enquadramento da foto de perfil (change recorte-foto-perfil).
// Envolvido pelo Reflex em doafacil/recorte_foto.py (ImageCropper).
//
// O enquadramento (crop) e o zoom ficam só no navegador, para o arraste ser
// fluido. O Reflex recebe apenas a área final (croppedAreaPixels) no fim de
// cada gesto, pelo onCropComplete. As setas vêm do próprio react-easy-crop
// (na área focável); as teclas + e - e os botões mudam o zoom.
import React, { useCallback, useEffect, useState } from "react";
import Cropper from "react-easy-crop";

const GREEN = "#007A42";
const TEXT = "#1F1F1F";
const BUTTON_BORDER = "#85858D";
const TRACK = "#C8C8C8";

// Estilo do controle de zoom no padrão do site: trilha cinza clara com a parte
// preenchida em verde, marcador redondo de 20 px branco com borda verde e
// anel de foco verde (também nos botões e na área de enquadramento, no lugar
// do azul padrão do navegador). O preenchimento vem da variável --fill.
const STYLES = `
.image-cropper-zoom {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  height: 44px;
  margin: 0;
  cursor: pointer;
}
.image-cropper-zoom::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(to right, ${GREEN} 0, ${GREEN} var(--fill, 0%), ${TRACK} var(--fill, 0%), ${TRACK} 100%);
}
.image-cropper-zoom::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  margin-top: -7px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 2px solid ${GREEN};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
.image-cropper-zoom::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: ${TRACK};
}
.image-cropper-zoom::-moz-range-progress {
  height: 6px;
  border-radius: 999px;
  background: ${GREEN};
}
.image-cropper-zoom::-moz-range-thumb {
  box-sizing: border-box;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 2px solid ${GREEN};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
.image-cropper-zoom:focus { outline: none; }
.image-cropper-zoom:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px #FFFFFF, 0 0 0 5px ${GREEN};
}
.image-cropper-zoom:focus-visible::-moz-range-thumb {
  box-shadow: 0 0 0 3px #FFFFFF, 0 0 0 5px ${GREEN};
}
.image-cropper-button:focus { outline: none; }
.image-cropper-button:focus-visible,
.image-cropper .reactEasyCrop_CropArea:focus-visible {
  outline: 2px solid ${GREEN};
  outline-offset: 2px;
}
.image-cropper .reactEasyCrop_CropArea:focus { outline: none; }
.image-cropper .reactEasyCrop_CropArea:focus-visible { outline-offset: -4px; }
.image-cropper-button:disabled { opacity: 0.5; cursor: default; }
`;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

const buttonStyle = {
  width: "44px",
  height: "44px",
  minWidth: "44px",
  borderRadius: "999px",
  border: `1px solid ${BUTTON_BORDER}`,
  background: "#FFFFFF",
  color: TEXT,
  fontSize: "1.4rem",
  lineHeight: 1,
  cursor: "pointer",
};

export default function ImageCropper({
  image,
  minZoom = 1,
  maxZoom = 3,
  zoomStep = 0.1,
  areaLabel,
  zoomLabel,
  zoomOutLabel,
  zoomInLabel,
  onCropComplete,
}) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(minZoom);

  // Uma foto nova começa centrada e sem zoom.
  useEffect(() => {
    setCrop({ x: 0, y: 0 });
    setZoom(minZoom);
  }, [image, minZoom]);

  const changeZoom = useCallback(
    (delta) => setZoom((current) => clamp(current + delta, minZoom, maxZoom)),
    [minZoom, maxZoom],
  );

  const handleComplete = useCallback(
    (_area, pixels) => {
      if (onCropComplete && pixels) {
        onCropComplete({
          x: pixels.x,
          y: pixels.y,
          width: pixels.width,
          height: pixels.height,
        });
      }
    },
    [onCropComplete],
  );

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "+" || event.key === "=") {
        event.preventDefault();
        changeZoom(zoomStep);
      } else if (event.key === "-" || event.key === "_") {
        event.preventDefault();
        changeZoom(-zoomStep);
      }
    },
    [changeZoom, zoomStep],
  );

  const fill = maxZoom > minZoom ? ((zoom - minZoom) / (maxZoom - minZoom)) * 100 : 0;

  return (
    <div
      className="image-cropper"
      onKeyDown={handleKeyDown}
      style={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%" }}
    >
      <style>{STYLES}</style>
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "400px",
          aspectRatio: "1 / 1",
          margin: "0 auto",
          background: TEXT,
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        {image ? (
          <Cropper
            image={image}
            crop={crop}
            zoom={zoom}
            minZoom={minZoom}
            maxZoom={maxZoom}
            aspect={1}
            cropShape="round"
            showGrid={false}
            restrictPosition={true}
            zoomWithScroll={true}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={handleComplete}
            cropperProps={{ role: "application", "aria-label": areaLabel }}
            mediaProps={{ alt: "" }}
          />
        ) : null}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%" }}>
        <button
          type="button"
          className="image-cropper-button"
          aria-label={zoomOutLabel}
          title={zoomOutLabel}
          onClick={() => changeZoom(-zoomStep)}
          disabled={zoom <= minZoom}
          style={buttonStyle}
        >
          −
        </button>
        <input
          type="range"
          className="image-cropper-zoom"
          aria-label={zoomLabel}
          min={minZoom}
          max={maxZoom}
          step={zoomStep}
          value={zoom}
          onChange={(event) => setZoom(clamp(Number(event.target.value), minZoom, maxZoom))}
          style={{ flex: "1 1 auto", minWidth: 0, "--fill": `${fill}%` }}
        />
        <button
          type="button"
          className="image-cropper-button"
          aria-label={zoomInLabel}
          title={zoomInLabel}
          onClick={() => changeZoom(zoomStep)}
          disabled={zoom >= maxZoom}
          style={buttonStyle}
        >
          +
        </button>
      </div>
    </div>
  );
}
