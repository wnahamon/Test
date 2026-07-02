import { useState, useEffect, useCallback } from "react";

// === ТИПЫ ===
type Status = "new" | "in_progress" | "done";
type Priority = "low" | "normal" | "high";

interface Item {
  id: number;
  title: string;
  description: string;
  status: Status;
  priority: Priority;
  created_at: string;
  updated_at: string;
}

interface User {
  username: string;
  is_admin: boolean;
}

// === КОНСТАНТЫ ===
const API_URL = "http://127.0.0.1:8000";

// === КОМПОНЕНТ ПРИЛОЖЕНИЯ ===
export default function App() {
  // Состояния авторизации
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token"),
  );
  const [user, setUser] = useState<User | null>(null);

  // Состояния данных
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Состояния фильтров и форм
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<Status | "">("");
  const [filterPriority, setFilterPriority] = useState<Priority | "">("");
  const [sortBy, setSortBy] = useState<"created_at" | "priority">("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Состояние формы создания
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [showForm, setShowForm] = useState(false);

  // Загрузка токена при старте
  useEffect(() => {
    if (token) fetchUser();
  }, [token]);

  // Загрузка списка заявок
  const loadItems = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        skip: "0",
        limit: "100",
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (search) params.set("search", search);
      if (filterStatus) params.set("status", filterStatus);
      if (filterPriority) params.set("priority", filterPriority);

      const res = await fetch(`${API_URL}/application/items?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Ошибка загрузки заявок");
      const data = await res.json();
      setItems(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token, search, filterStatus, filterPriority, sortBy, sortOrder]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // Получение информации о пользователе
  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token!}` },
      });
      if (res.ok) setUser(await res.json());
      else logout();
    } catch {
      logout();
    }
  };

  // Авторизация
  const login = async (username: string, password: string) => {
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) throw new Error("Неверный логин или пароль");
      const data = await res.json();

      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  // CRUD операции
  const createItem = async () => {
    if (!newTitle.trim()) return alert("Введите заголовок");
    try {
      await fetch(`${API_URL}/application/items`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token!}`,
        },
        body: JSON.stringify({ title: newTitle, description: newDesc }),
      });
      setNewTitle("");
      setNewDesc("");
      setShowForm(false);
      loadItems();
    } catch {
      alert("Ошибка создания");
    }
  };

  const updateStatus = async (id: number, status: Status) => {
    try {
      await fetch(
        `${API_URL}/application/items/${id}/status?status=${status}`,
        {
          method: "PATCH",
          headers: { Authorization: `Bearer ${token!}` },
        },
      );
      loadItems();
    } catch {
      alert("Ошибка обновления статуса");
    }
  };

  const deleteItem = async (id: number) => {
    if (!confirm("Удалить заявку?")) return;
    try {
      await fetch(`${API_URL}/application/items/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token!}` },
      });
      loadItems();
    } catch {
      alert("Ошибка удаления");
    }
  };

  if (!token) {
    return (
      <div style={styles.container}>
        <h2>Вход в систему</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            login(
              (e.target as any).username.value,
              (e.target as any).password.value,
            );
          }}
        >
          <input
            name="username"
            placeholder="Логин"
            required
            style={styles.input}
          />
          <input
            name="password"
            type="password"
            placeholder="Пароль"
            required
            style={styles.input}
          />
          <button type="submit" style={styles.btnPrimary}>
            Войти
          </button>
        </form>
      </div>
    );
  }

  // === РЕНДЕР ГЛАВНОЙ СТРАНИЦЫ ===
  return (
    <div style={styles.container}>
      {/* Шапка */}
      <div style={styles.header}>
        <h3>Система заявок ({user?.is_admin ? "Админ" : "Пользователь"})</h3>
        <button onClick={logout} style={styles.btnDanger}>
          Выход
        </button>
      </div>

      {/* Панель управления */}
      <div style={styles.controls}>
        <input
          placeholder="Поиск по названию..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.input}
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as any)}
          style={styles.select}
        >
          <option value="">Все статусы</option>
          <option value="new">Новая</option>
          <option value="in_progress">В работе</option>
          <option value="done">Готова</option>
        </select>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as any)}
          style={styles.select}
        >
          <option value="">Все приоритеты</option>
          <option value="low">Низкий</option>
          <option value="normal">Средний</option>
          <option value="high">Высокий</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          style={styles.select}
        >
          <option value="created_at">По дате</option>
          <option value="priority">По приоритету</option>
        </select>
        <button
          onClick={() => setSortOrder((o) => (o === "asc" ? "desc" : "asc"))}
          style={styles.btnSecondary}
        >
          {sortOrder === "asc" ? "↑" : "↓"}
        </button>
        <button
          onClick={() => setShowForm(!showForm)}
          style={styles.btnPrimary}
        >
          + Новая заявка
        </button>
      </div>

      {/* Форма создания */}
      {showForm && (
        <div style={styles.formCard}>
          <input
            placeholder="Заголовок"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            style={styles.input}
          />
          <textarea
            placeholder="Описание"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            style={{ ...styles.input, minHeight: 60 }}
          />
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={createItem} style={styles.btnPrimary}>
              Создать
            </button>
            <button
              onClick={() => setShowForm(false)}
              style={styles.btnSecondary}
            >
              Отмена
            </button>
          </div>
        </div>
      )}

      {/* Список заявок */}
      {loading ? (
        <p>Загрузка...</p>
      ) : error ? (
        <p style={{ color: "red" }}>{error}</p>
      ) : (
        <div style={styles.list}>
          {items.length === 0 && <p>Заявок не найдено</p>}
          {items.map((item) => (
            <div key={item.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <strong>{item.title}</strong>
                <span
                  style={{
                    ...styles.badge,
                    background:
                      item.status === "done"
                        ? "#d1fae5"
                        : item.status === "in_progress"
                          ? "#fef3c7"
                          : "#e0f2fe",
                    color:
                      item.status === "done"
                        ? "#065f46"
                        : item.status === "in_progress"
                          ? "#92400e"
                          : "#0369a1",
                  }}
                >
                  {item.status === "new"
                    ? "Новая"
                    : item.status === "in_progress"
                      ? "В работе"
                      : "Готова"}
                </span>
              </div>
              <p style={styles.desc}>{item.description}</p>
              <div style={styles.cardFooter}>
                <small>
                  Приоритет:{" "}
                  {item.priority === "high"
                    ? "Высокий"
                    : item.priority === "normal"
                      ? "Средний"
                      : "Низкий"}
                </small>
                <div style={{ display: "flex", gap: 6 }}>
                  {item.status !== "done" && (
                    <select
                      defaultValue=""
                      onChange={(e) => {
                        if (e.target.value)
                          updateStatus(item.id, e.target.value as Status);
                      }}
                      style={{
                        ...styles.select,
                        padding: "2px 6px",
                        fontSize: 12,
                      }}
                    >
                      <option value="" disabled>
                        Изменить статус
                      </option>
                      <option value="in_progress">В работу</option>
                      <option value="done">Завершить</option>
                    </select>
                  )}
                  {user?.is_admin && item.status !== "done" && (
                    <button
                      onClick={() => deleteItem(item.id)}
                      style={styles.btnDangerSmall}
                    >
                      Удалить
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 800,
    margin: "40px auto",
    padding: 20,
    fontFamily: "system-ui, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  controls: { display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  formCard: {
    background: "#f8fafc",
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  list: { display: "flex", flexDirection: "column", gap: 12 },
  card: {
    border: "1px solid #e2e8f0",
    borderRadius: 8,
    padding: 16,
    background: "#fff",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  cardFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    borderTop: "1px solid #f1f5f9",
    paddingTop: 8,
  },
  desc: { margin: 0, color: "#64748b", fontSize: 14 },
  badge: {
    padding: "2px 8px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
  },
  input: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    outline: "none",
  },
  select: {
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    background: "#fff",
  },
  btnPrimary: {
    padding: "8px 16px",
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontWeight: 500,
  },
  btnSecondary: {
    padding: "8px 16px",
    background: "#e2e8f0",
    color: "#1e293b",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
  },
  btnDanger: {
    padding: "8px 16px",
    background: "#ef4444",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
  },
  btnDangerSmall: {
    padding: "4px 10px",
    background: "#fee2e2",
    color: "#dc2626",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 12,
  },
};
