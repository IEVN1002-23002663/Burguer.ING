import { HttpErrorResponse } from '@angular/common/http';

export function mensajeError(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No hay conexión con Flask. Comprueba que esté encendido en el puerto 5000 y que CORS esté configurado.';
    }
    const body = error.error as { mensaje?: string; error?: string } | null;
    return body?.mensaje || `Error HTTP ${error.status}. Revisa la ruta de Flask.`;
  }
  return 'Ocurrió un error inesperado.';
}
