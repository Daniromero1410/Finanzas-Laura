document.getElementById("expenseForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const categoria = document.getElementById("categoria").value;
    const descripcion = document.getElementById("descripcion").value;
    const monto = document.getElementById("monto").value;
    const mes = document.getElementById("mes").value;

    fetch("http://localhost:5000/add_expense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ categoria, descripcion, monto, mes })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("mensaje").textContent = data.message;
    })
    .catch(error => {
        document.getElementById("mensaje").textContent = "Error al agregar el gasto";
        console.error("Error:", error);
    });
});