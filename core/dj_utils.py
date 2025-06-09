from typing import List, Optional


def get_compatible_camelot_keys(key: Optional[str]) -> List[str]:
    """
    Calcula las claves Camelot armónicamente compatibles.

    Args:
        key (str): La clave Camelot de origen (ej. "8B", "5A").

    Returns:
        List[str]: Una lista de claves compatibles.
    """
    if not key or len(key) < 2 or not key[:-1].isdigit():
        return []

    try:
        number = int(key[:-1])
        mode = key[-1].upper()

        if mode not in ["A", "B"]:
            return []

        compatible_keys = []

        # 1. La misma clave
        compatible_keys.append(f"{number}{mode}")

        # 2. Relativo mayor/menor
        relative_mode = "A" if mode == "B" else "B"
        compatible_keys.append(f"{number}{relative_mode}")

        # 3. Una clave hacia arriba
        up_number = 1 if number == 12 else number + 1
        compatible_keys.append(f"{up_number}{mode}")

        # 4. Una clave hacia abajo
        down_number = 12 if number == 1 else number - 1
        compatible_keys.append(f"{down_number}{mode}")

        return list(set(compatible_keys))  # Usar set para eliminar duplicados

    except (ValueError, IndexError):
        return []


if __name__ == "__main__":
    # Pruebas rápidas
    print(f"8B -> {get_compatible_camelot_keys('8B')}")
    print(f"1A -> {get_compatible_camelot_keys('1A')}")
    print(f"12A -> {get_compatible_camelot_keys('12A')}")
    print(f"Invalido -> {get_compatible_camelot_keys('13C')}")
    print(f"None -> {get_compatible_camelot_keys(None)}")
