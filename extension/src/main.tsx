import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

function renderApp() {
  const rootElement = document.getElementById("root");
  if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      const el = document.getElementById("root");
      if (el) {
        ReactDOM.createRoot(el).render(
          <React.StrictMode>
            <App />
          </React.StrictMode>
        );
      }
    });
  }
}

renderApp();
