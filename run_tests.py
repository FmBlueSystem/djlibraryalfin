import unittest
import os

def run_all_tests():
    """
    Descubre y ejecuta todas las pruebas en el directorio 'tests'.
    """
    # Empezar el descubrimiento desde el directorio raíz del proyecto
    start_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(start_dir, 'tests')
    
    print(f"Buscando pruebas en: {test_dir}")

    # Descubrir todas las pruebas que coincidan con el patrón 'test_*.py'
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')
    
    # Ejecutar las pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Salir con un código de error si alguna prueba falló
    if not result.wasSuccessful():
        exit(1)

if __name__ == '__main__':
    run_all_tests() 