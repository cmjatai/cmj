<template>
  <div class="http-404">
    <img
      src="/imgs/logo_emendamais.svg"
      alt="Logo Emenda"
      class="img-fluid"
    >
    <div class="error-container">
      <h1 class="error-code">
        404
      </h1>
      <h2 class="error-title">
        Página não encontrada
      </h2>
      <p class="error-message">
        A página que você está procurando não existe ou foi movida.
      </p>
      <a
        href="/"
        class="home-button"
      >
        Voltar para página inicial
      </a>
    </div>
  </div>
</template>
<style scoped>
.http-404 {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 2rem;
}

.error-container {
  text-align: center;
  padding: 1rem;
  max-width: 500px;
}

.error-code {
  font-size: 8rem;
  margin: 0;
  color: #dc3545;
  font-weight: bold;
}

.error-title {
  font-size: 2rem;
  margin-top: 0.5rem;
  color: #343a40;
}

.error-message {
  margin: 1.5rem 0;
  color: #6c757d;
  font-size: 1.1rem;
}

.home-button {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.home-button:hover {
  background-color: #0069d9;
}

@media screen and (min-width: 768px) {
  .img-fluid {
    max-width: 50%;
  }
}
</style>
