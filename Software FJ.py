import datetime
from abc import ABC, abstractmethod


# =========================================================================
# 1. CAPA DE PERSISTENCIA (MANEJO DE ARCHIVOS / LOGS)
# Requisito: Registro de eventos y errores sin base de datos.
# =========================================================================

def registrar_log(mensaje):
    """
    Función para persistencia de datos en archivos planos.
    Registra errores y éxitos para auditoría del sistema.
    """
    try:
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Se abre en modo 'a' (append) para no borrar registros anteriores
        with open("log_sistema.txt", "a") as archivo:
            archivo.write(f"[{ahora}] {mensaje}\n")
    except Exception as e:
        # Si falla la escritura (ej. falta de permisos), se informa por consola
        print(f"Error crítico al escribir en el log: {e}")


# =========================================================================
# 2. CAPA DE EXCEPCIONES PERSONALIZADAS
# Requisito: Manejo avanzado y específico de errores de negocio.
# =========================================================================

class ErrorSoftwareFJ(Exception):
    """Clase base (Padre) para todas las excepciones del proyecto."""
    pass


class ReservaInvalidaError(ErrorSoftwareFJ):
    """Excepción para errores de lógica en la creación o manipulación de reservas."""
    pass


class DatosClienteError(ErrorSoftwareFJ):
    """Excepción para fallos en la validación de integridad del cliente."""
    pass


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """Excepción para intentos de usar un servicio no disponible."""
    pass


# =========================================================================
# 3. CAPA DE MODELO (ARQUITECTURA ORIENTADA A OBJETOS)
# =========================================================================

class Entidad(ABC):
    """
    CLASE ABSTRACTA: Representa la base de cualquier objeto en el sistema.
    Aplica el principio de Abstracción.
    """

    def __init__(self, id_entidad):
        # Atributo protegido (Encapsulamiento simple)
        self._id_entidad = id_entidad

    @abstractmethod
    def mostrar_info(self):
        """Método abstracto que obliga a las hijas a identificarse."""
        pass


class Cliente(Entidad):
    """
    Clase Cliente: Gestiona la información del usuario con validaciones.
    Aplica Encapsulamiento Estricto (atributos privados __).
    """

    def __init__(self, id_cliente, nombre, correo):
        super().__init__(id_cliente)
        self.__nombre = nombre

        # VALIDACIÓN ROBUSTA: No permite crear el objeto si el correo no es válido
        if "@" not in correo or "." not in correo:
            raise DatosClienteError(f"Formato de correo inválido: {correo}")
        self.__correo = correo

    def mostrar_info(self):
        return f"Cliente: {self.__nombre} (ID: {self._id_entidad})"

    @property  # Decorador para acceder al atributo privado de forma segura
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo


# =========================================================================
# 4. JERARQUÍA DE SERVICIOS (POLIMORFISMO Y SOBRECARGA)
# =========================================================================

class Servicio(ABC):
    """
    CLASE ABSTRACTA SERVICIO: Define la estructura para los tipos de servicios.
    """

    def __init__(self, nombre_servicio, precio_base):
        self.nombre_servicio = nombre_servicio
        self.precio_base = precio_base

    @abstractmethod
    def calcular_costo(self, *args, **kwargs):
        """Método polimórfico: cada servicio lo implementa diferente."""
        pass

    @abstractmethod
    def descripcion(self):
        """Método para describir el servicio (requisito de negocio)."""
        pass


class ReservaSala(Servicio):
    """
    Servicio de reserva de sala con impuesto por defecto.
    Aplica sobrecarga a través de parámetro opcional `impuesto`.
    """

    def calcular_costo(self, horas, impuesto=0.19):
        """
        Calcula el costo de una reserva de sala por horas.
        Valida que las horas sean positivas.
        """
        if horas < 0:
            raise ValueError("Las horas no pueden ser negativas.")
        return (self.precio_base * horas) * (1 + impuesto)

    def descripcion(self):
        return f"Reserva de sala: ${self.precio_base:.2f} por hora + impuesto del 19%."


class AlquilerEquipo(Servicio):
    """
    Servicio de alquiler de equipo con descuento opcional.
    Aplica sobrecarga con parámetro opcional `descuento`.
    """

    def calcular_costo(self, dias, descuento=0):
        """
        Calcula el costo del alquiler por días, restando un descuento opcional.
        Valida que los días sean positivos.
        """
        if dias < 0:
            raise ValueError("Los días no pueden ser negativos.")
        costo = (self.precio_base * dias) - descuento
        return max(0, costo)

    def descripcion(self):
        return f"Alquiler de equipo: ${self.precio_base:.2f} por día, descuento opcional."


class AsesoriaEspecializada(Servicio):
    """
    Servicio de asesoría especializada por sesiones.
    Implementa polimorfismo simple por número de sesiones.
    """

    def calcular_costo(self, sesiones):
        """
        Calcula el costo por número de sesiones.
        Valida que las sesiones sean positivas.
        """
        if sesiones < 0:
            raise ValueError("Las sesiones no pueden ser negativas.")
        return self.precio_base * sesiones

    def descripcion(self):
        return f"Asesoría especializada: ${self.precio_base:.2f} por sesión."


# =========================================================================
# 4. CLASE RESERVA (CONECTA CLIENTE, SERVICIO Y ESTADO)
# Requisito: Manejo avanzado de excepciones y estados (confirmar/cancelar).
# =========================================================================

class Reserva:
    ESTADOS_VALIDOS = {"Pendiente", "Confirmada", "Cancelada", "Fallida", "Error de Sistema"}

    def __init__(self, cliente, servicio, duracion):
        """
        Representa una reserva vinculando cliente, servicio y duración.
        `duracion` puede ser horas, días o sesiones según el servicio.
        """
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "Pendiente"

    def procesar_reserva(self):
        """
        Ejecuta el registro y cálculo de la reserva con manejo robusto de errores.
        Usa try/except/else/finally y encadenamiento de excepciones.
        """
        try:
            # 1. Validaciones preventivas generales
            if not self.cliente:
                raise ValueError("La reserva requiere un cliente registrado.")

            if not self.servicio:
                raise ValueError("La reserva requiere un servicio definido.")

            if self.duracion < 0:
                raise ValueError("La duración/cantidad debe ser mayor o igual a cero.")

            # 2. Validación específica del servicio (evita cálculos inconsistentes)
            if self.servicio.nombre_servicio == "Reserva de Sala":
                self.servicio.calcular_costo(self.duracion)
            elif self.servicio.nombre_servicio == "Alquiler de Laptop":
                self.servicio.calcular_costo(self.duracion)
            elif self.servicio.nombre_servicio == "Asesoría IT":
                self.servicio.calcular_costo(self.duracion)

            # 3. Aplicación de POLIMORFISMO: El objeto 'servicio' sabe qué fórmula usar
            costo_final = self.servicio.calcular_costo(self.duracion)

        except ValueError as e:
            # ENCADENAMIENTO DE EXCEPCIONES: Se captura un error común y se lanza uno personalizado
            self.estado = "Fallida"
            error_msg = f"Parámetro inválido en reserva: {e}"
            registrar_log(f"RESERVA RECHAZADA: {error_msg}")
            raise ReservaInvalidaError(error_msg) from e

        except ServicioNoDisponibleError as e:
            self.estado = "Fallida"
            registrar_log(f"SERVICIO NO DISPONIBLE: {e}")
            raise

        except Exception as e:
            # Captura de cualquier otro error no previsto (Robustez)
            self.estado = "Error de Sistema"
            registrar_log(f"EXCEPCIÓN NO CONTROLADA: {e}")
            print(f"Error inesperado: {type(e).__name__}: {e}")

        else:
            # BLOQUE ELSE: Se ejecuta SOLO si el bloque TRY fue exitoso
            self.estado = "Confirmada"
            msg_exito = (
                f"ÉXITO: {self.servicio.nombre_servicio} para {self.cliente.nombre} - "
                f"Total: ${costo_final:.2f}"
            )
            registrar_log(msg_exito)
            print(msg_exito)

        finally:
            # BLOQUE FINALLY: Se ejecuta SIEMPRE (limpieza o cierre de procesos)
            print(f"Finalización de proceso: {self.estado}\n")

    def confirmar(self):
        """
        Permite confirmar explícitamente una reserva pendiente.
        """
        if self.estado != "Pendiente":
            raise ReservaInvalidaError(
                f"No se puede confirmar una reserva en estado '{self.estado}'."
            )
        self.estado = "Confirmada"
        registrar_log(f"CONFIRMACIÓN MANUAL: Reserva confirmada para {self.cliente.nombre}.")

    def cancelar(self):
        """
        Cambia el estado a cancelada si la reserva está confirmada.
        """
        if self.estado == "Confirmada":
            self.estado = "Cancelada"
            registrar_log(f"CANCELACIÓN: Reserva cancelada para {self.cliente.nombre}.")
        elif self.estado in {"Fallida", "Error de Sistema", "Cancelada"}:
            pass  # No hace nada, ya está en estado no cancelable o cancelado
        else:
            raise ReservaInvalidaError(
                f"No se puede cancelar una reserva en estado '{self.estado}'."
            )


# =========================================================================
# 5. GESTOR CENTRAL (SOFTWARE FJ) - LISTAS INTERNAS
# Requisito: Gestión de clientes, servicios y reservas mediante listas internas.
# =========================================================================

class GestorSoftwareFJ:
    """
    Clase central que gestiona clientes, servicios y reservas de Software FJ.
    Emplea listas internas para almacenar objetos sin base de datos.
    """

    def __init__(self):
        self.lista_clientes = []
        self.lista_servicios = []
        self.lista_reservas = []

    def agregar_cliente(self, cliente):
        """Agrega un cliente a la lista interna."""
        if cliente not in self.lista_clientes:
            self.lista_clientes.append(cliente)
        registrar_log(f"CLIENTE AGREGADO: {cliente.mostrar_info()}")

    def agregar_servicio(self, servicio):
        """Agrega un servicio a la lista interna."""
        if servicio not in self.lista_servicios:
            self.lista_servicios.append(servicio)
        registrar_log(f"SERVICIO AGREGADO: {servicio.nombre_servicio}")

    def registrar_reserva(self, cliente, servicio, duracion):
        """
        Crea y registra una nueva reserva, validando que el cliente y servicio existan.
        """
        if cliente not in self.lista_clientes:
            raise DatosClienteError("Cliente no registrado en el sistema.")
        if servicio not in self.lista_servicios:
            raise ServicioNoDisponibleError("Servicio no registrado en el sistema.")

        reserva = Reserva(cliente, servicio, duracion)
        self.lista_reservas.append(reserva)
        registrar_log(
            f"RESERVA REGISTRADA: {servicio.nombre_servicio} para {cliente.nombre} "
            f"duración {duracion}. Estado inicial: {reserva.estado}"
        )
        return reserva

    def listar_reservas(self):
        """Muestra en consola todas las reservas registradas."""
        print("\n=== LISTADO DE RESERVAS ===")
        if not self.lista_reservas:
            print("No hay reservas registradas.")
        for idx, r in enumerate(self.lista_reservas, 1):
            print(
                f"{idx}. {r.servicio.nombre_servicio} | "
                f"Cliente: {r.cliente.nombre} | "
                f"Duración: {r.duracion} | "
                f"Estado: {r.estado}"
            )


# =========================================================================
# 6. SIMULACIÓN DE 10 OPERACIONES (PRUEBA DE ESTABILIDAD)
# Requisito: Demostrar que el sistema no se detiene ante errores graves.
# =========================================================================

def ejecutar_simulacion_automatica():
    print("=========================================================")
    print("--- SISTEMA INTEGRAL SOFTWARE FJ - FASE 4 ---")
    print("Simulación de 10 Operaciones (Válidas e Inválidas)")
    print("=========================================================\n")

    # Instanciación del gestor
    gestor = GestorSoftwareFJ()

    # Instanciación de servicios
    s_sala = ReservaSala("Reserva de Sala", 60000)
    s_equipo = AlquilerEquipo("Alquiler de Laptop", 45000)
    s_asesoria = AsesoriaEspecializada("Asesoría IT", 120000)

    # Registrar servicios en el gestor
    gestor.agregar_servicio(s_sala)
    gestor.agregar_servicio(s_equipo)
    gestor.agregar_servicio(s_asesoria)

    # Creación de clientes
    clientes = []
    try:
        clientes.append(Cliente("C01", "Juan David", "juan@unad.edu.co"))
        clientes.append(Cliente("C02", "Maria Lopez", "maria@unad.edu.co"))
        # ERROR CONTROLADO: Cliente con formato de correo incorrecto
        clientes.append(Cliente("C03", "Pedro Error", "pedro_sin_arroba.com"))
    except DatosClienteError as e:
        # Se registra el error pero el programa CONTINÚA
        registrar_log(f"FALLO REGISTRO: {e}")
        print(f"Aviso de Validación: {e} (Operación controlada)\n")
        clientes.append(None)

    # Registrar clientes válidos en el gestor
    for c in clientes:
        if c is not None:
            gestor.agregar_cliente(c)

    # MATRIZ DE PRUEBA (10 OPERACIONES)
    # Mezcla casos de éxito con casos que dispararán excepciones
    operaciones = [
        (clientes[0], s_sala, 4),      # 1. Éxito
        (clientes[1], s_equipo, 2),    # 2. Éxito
        (clientes[0], s_sala, -2),     # 3. Fallo (Duración negativa)
        (clientes[1], s_asesoria, 5),  # 4. Éxito
        (clientes[2], s_equipo, 1),    # 5. Fallo (Cliente inexistente/None)
        (clientes[0], s_equipo, 3),    # 6. Éxito
        (clientes[1], s_sala, 2),      # 7. Éxito
        (clientes[0], s_asesoria, 0),  # 8. Fallo (Duración cero)
        (clientes[1], s_equipo, 1),    # 9. Éxito
        (clientes[0], s_sala, 5)       # 10. Éxito
    ]

    # Ejecución del bucle de simulación
    for i, (c, s, d) in enumerate(operaciones, 1):
        print(f"Operación #{i}:")
        try:
            # Registrar la reserva a través del gestor
            reserva = gestor.registrar_reserva(c, s, d)
            # Procesar la reserva (confirmación automática por lógica de negocio)
            reserva.procesar_reserva()

            # Ejemplo de usar confirmar/cancelar explícitamente
            if reserva.estado == "Confirmada" and i % 3 == 0:
                # Cada 3 operaciones exitosas, se prueba una cancelación
                reserva.cancelar()
                print(f"Reserva cancelada manualmente: {reserva.estado}\n")

        except ReservaInvalidaError as e:
            # Captura del error encadenado para mostrarlo en consola
            print(f"Resultado: {e}\n")
        except ErrorSoftwareFJ as e:
            # Captura general de errores del sistema
            print(f"Error del sistema: {e}\n")

    # Listar todas las reservas al final (demostración de listas internas)
    gestor.listar_reservas()


if __name__ == "__main__":
    ejecutar_simulacion_automatica()