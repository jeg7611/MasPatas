import { useEffect, useMemo, useState } from 'react';
import { api } from './api';
import './styles.css';

const defaultProduct = {
  product_id: '',
  name: '',
  sku: '',
  price_amount: '',
  currency: 'USD',
  initial_stock: 0,
};

const defaultClient = {
  client_id: '',
  full_name: '',
  email: '',
};

const defaultSale = {
  sale_id: '',
  client_id: '',
  lines: [{ product_id: '', quantity: 1 }],
};

function App() {
  const [token, setToken] = useState(localStorage.getItem('maspatas_token') ?? '');
  const [authForm, setAuthForm] = useState({ username: 'admin', password: 'maspatas123' });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [products, setProducts] = useState([]);
  const [clients, setClients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [sales, setSales] = useState([]);

  const [productForm, setProductForm] = useState(defaultProduct);
  const [clientForm, setClientForm] = useState(defaultClient);
  const [saleForm, setSaleForm] = useState(defaultSale);

  const totals = useMemo(() => {
    const stock = inventory.reduce((acc, item) => acc + item.stock, 0);
    const revenue = sales.reduce((acc, sale) => acc + Number(sale.total_amount), 0);
    return { stock, revenue };
  }, [inventory, sales]);

  const clearFeedback = () => {
    setMessage('');
    setError('');
  };

  const loadAll = async () => {
    setBusy(true);
    clearFeedback();
    try {
      const [productsRes, clientsRes, inventoryRes, salesRes] = await Promise.all([
        api.getProducts(),
        api.getClients(),
        api.getInventory(),
        api.getSales(),
      ]);
      setProducts(productsRes);
      setClients(clientsRes);
      setInventory(inventoryRes);
      setSales(salesRes);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const onLogin = async (event) => {
    event.preventDefault();
    setBusy(true);
    clearFeedback();
    try {
      const response = await api.getToken(authForm);
      setToken(response.access_token);
      localStorage.setItem('maspatas_token', response.access_token);
      setMessage('Sesión iniciada correctamente.');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onLogout = () => {
    setToken('');
    localStorage.removeItem('maspatas_token');
    setMessage('Sesión cerrada.');
  };

  const withGuard = async (handler) => {
    if (!token) {
      setError('Inicia sesión para ejecutar acciones protegidas.');
      return;
    }
    setBusy(true);
    clearFeedback();
    try {
      await handler();
      await loadAll();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const createProduct = async (event) => {
    event.preventDefault();
    await withGuard(async () => {
      await api.createProduct(token, {
        ...productForm,
        initial_stock: Number(productForm.initial_stock),
      });
      setProductForm(defaultProduct);
      setMessage('Producto registrado.');
    });
  };

  const createClient = async (event) => {
    event.preventDefault();
    await withGuard(async () => {
      await api.createClient(token, clientForm);
      setClientForm(defaultClient);
      setMessage('Cliente registrado.');
    });
  };

  const createSale = async (event) => {
    event.preventDefault();
    await withGuard(async () => {
      await api.createSale(token, {
        ...saleForm,
        lines: saleForm.lines.map((line) => ({
          ...line,
          quantity: Number(line.quantity),
        })),
      });
      setSaleForm(defaultSale);
      setMessage('Venta registrada.');
    });
  };

  const updateSaleLine = (index, key, value) => {
    setSaleForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) => (lineIndex === index ? { ...line, [key]: value } : line)),
    }));
  };

  return (
    <main className="layout">
      <header>
        <h1>MasPatas • Panel Operativo</h1>
        <p>Frontend en React para productos, clientes, inventario y ventas.</p>
      </header>

      <section className="card summary-grid">
        <div>
          <h3>{products.length}</h3>
          <p>Productos</p>
        </div>
        <div>
          <h3>{clients.length}</h3>
          <p>Clientes</p>
        </div>
        <div>
          <h3>{totals.stock}</h3>
          <p>Stock total</p>
        </div>
        <div>
          <h3>{totals.revenue.toFixed(2)}</h3>
          <p>Ingresos acumulados</p>
        </div>
      </section>

      <section className="card">
        <div className="section-title">
          <h2>Autenticación</h2>
          <button type="button" onClick={loadAll} disabled={busy}>
            Refrescar datos
          </button>
        </div>

        <form onSubmit={onLogin} className="row-form">
          <input
            placeholder="Usuario"
            value={authForm.username}
            onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })}
          />
          <input
            placeholder="Contraseña"
            type="password"
            value={authForm.password}
            onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
          />
          <button type="submit" disabled={busy}>
            Obtener token
          </button>
          {token && (
            <button type="button" className="secondary" onClick={onLogout}>
              Cerrar sesión
            </button>
          )}
        </form>
        {token && <small>Token activo: {token}</small>}
      </section>

      {message && <p className="message ok">{message}</p>}
      {error && <p className="message error">{error}</p>}

      <div className="grid-2">
        <section className="card">
          <h2>Registrar producto</h2>
          <form onSubmit={createProduct} className="column-form">
            <input placeholder="ID" value={productForm.product_id} onChange={(event) => setProductForm({ ...productForm, product_id: event.target.value })} required />
            <input placeholder="Nombre" value={productForm.name} onChange={(event) => setProductForm({ ...productForm, name: event.target.value })} required />
            <input placeholder="SKU" value={productForm.sku} onChange={(event) => setProductForm({ ...productForm, sku: event.target.value })} required />
            <input placeholder="Precio" value={productForm.price_amount} onChange={(event) => setProductForm({ ...productForm, price_amount: event.target.value })} required />
            <input placeholder="Moneda" maxLength={3} value={productForm.currency} onChange={(event) => setProductForm({ ...productForm, currency: event.target.value.toUpperCase() })} required />
            <input type="number" min="0" placeholder="Stock inicial" value={productForm.initial_stock} onChange={(event) => setProductForm({ ...productForm, initial_stock: event.target.value })} required />
            <button disabled={busy}>Guardar producto</button>
          </form>
        </section>

        <section className="card">
          <h2>Registrar cliente</h2>
          <form onSubmit={createClient} className="column-form">
            <input placeholder="ID" value={clientForm.client_id} onChange={(event) => setClientForm({ ...clientForm, client_id: event.target.value })} required />
            <input placeholder="Nombre completo" value={clientForm.full_name} onChange={(event) => setClientForm({ ...clientForm, full_name: event.target.value })} required />
            <input placeholder="Email" type="email" value={clientForm.email} onChange={(event) => setClientForm({ ...clientForm, email: event.target.value })} required />
            <button disabled={busy}>Guardar cliente</button>
          </form>
        </section>
      </div>

      <section className="card">
        <h2>Registrar venta</h2>
        <form onSubmit={createSale} className="column-form">
          <input placeholder="ID venta" value={saleForm.sale_id} onChange={(event) => setSaleForm({ ...saleForm, sale_id: event.target.value })} required />
          <select value={saleForm.client_id} onChange={(event) => setSaleForm({ ...saleForm, client_id: event.target.value })} required>
            <option value="">Selecciona cliente</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.full_name} ({client.id})
              </option>
            ))}
          </select>

          {saleForm.lines.map((line, index) => (
            <div key={index} className="sale-line">
              <select value={line.product_id} onChange={(event) => updateSaleLine(index, 'product_id', event.target.value)} required>
                <option value="">Producto</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                value={line.quantity}
                onChange={(event) => updateSaleLine(index, 'quantity', event.target.value)}
                required
              />
            </div>
          ))}

          <button
            type="button"
            className="secondary"
            onClick={() => setSaleForm((current) => ({ ...current, lines: [...current.lines, { product_id: '', quantity: 1 }] }))}
          >
            Agregar línea
          </button>
          <button disabled={busy}>Guardar venta</button>
        </form>
      </section>

      <div className="grid-2">
        <section className="card list-card">
          <h2>Inventario</h2>
          <ul>
            {inventory.map((item) => (
              <li key={item.product_id}>
                {item.product_id}: {item.stock}
              </li>
            ))}
          </ul>
        </section>

        <section className="card list-card">
          <h2>Ventas</h2>
          <ul>
            {sales.map((sale) => (
              <li key={sale.sale_id}>
                {sale.sale_id} · Cliente {sale.client_id} · {sale.total_amount} {sale.currency}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}

export default App;
