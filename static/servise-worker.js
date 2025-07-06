self.addEventListener("install", e => {
  console.log("Service Worker instalado");
});

self.addEventListener("fetch", function(event) {
  // Cache opcional o lógica personalizada
});
