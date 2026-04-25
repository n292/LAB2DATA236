export function getApiErrorMessage(error, fallback = "Something went wrong") {
  const data = error?.response?.data;

  const detail =
    data?.detail ||
    data?.message ||
    error?.detail ||
    error?.message ||
    error;

  if (!detail) {
    return fallback;
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item?.msg) {
          const location = Array.isArray(item.loc)
            ? item.loc.join(".")
            : item.loc;

          return location ? `${location}: ${item.msg}` : item.msg;
        }

        return JSON.stringify(item);
      })
      .join(" | ");
  }

  if (typeof detail === "object") {
    if (detail.msg) {
      const location = Array.isArray(detail.loc)
        ? detail.loc.join(".")
        : detail.loc;

      return location ? `${location}: ${detail.msg}` : detail.msg;
    }

    return JSON.stringify(detail);
  }

  return fallback;
}

export function formatDisplayError(value, fallback = "Something went wrong") {
  if (!value) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item?.msg) {
          const location = Array.isArray(item.loc)
            ? item.loc.join(".")
            : item.loc;

          return location ? `${location}: ${item.msg}` : item.msg;
        }

        return JSON.stringify(item);
      })
      .join(" | ");
  }

  if (typeof value === "object") {
    if (value.msg) {
      const location = Array.isArray(value.loc)
        ? value.loc.join(".")
        : value.loc;

      return location ? `${location}: ${value.msg}` : value.msg;
    }

    return JSON.stringify(value);
  }

  return fallback;
}