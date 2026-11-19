import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  templateUrl: './icon.html'
})
export class Icon {
  @Input() name = 'box';
  @Input() size = 18;
  readonly icons: Record<string,string> = {
    dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    users: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8a4 4 0 0 0 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    truck: 'M3 7h11v11H3z M14 11h4l3 3v4h-7z M8 21a2 2 0 1 0 0-4a2 2 0 0 0 0 4 M18 21a2 2 0 1 0 0-4a2 2 0 0 0 0 4',
    cart: 'M2 3h2l3 12h12l3-9H5 M9 21a1 1 0 1 0 0-2a1 1 0 0 0 0 2 M18 21a1 1 0 1 0 0-2a1 1 0 0 0 0 2',
    box: 'M3 7l9-4l9 4v10l-9 4l-9-4z M3 7l9 4l9-4 M12 11v10',
    warehouse: 'M3 10l9-7l9 7v11H3z M8 21v-9h8v9 M8 16h8',
    search: 'M11 19a8 8 0 1 0 0-16a8 8 0 0 0 0 16 M21 21l-4.4-4.4',
    bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4',
    logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5l-5-5 M21 12H9',
    plus: 'M12 5v14 M5 12h14',
    edit: 'M12 20h9 M16 4l4 4l-11 11l-5 1l1-5z',
    trash: 'M3 6h18 M8 6V4h8v2 M6 6l1 15h10l1-15 M10 10v7 M14 10v7',
    check: 'M20 6L9 17l-5-5',
    warning: 'M12 3l10 18H2z M12 9v5 M12 18h.01',
    close: 'M18 6L6 18 M6 6l12 12',
    money: 'M12 2v20 M16 6a5 5 0 0 0-8 0c-3 5 13 3 8 10a5 5 0 0 1-8 0',
    chart: 'M3 3v18h18 M7 15l4-5l4 3l5-8',
    menu: 'M4 6h16 M4 12h16 M4 18h16',
    refresh: 'M20 11a8 8 0 1 0-2 6 M20 4v7h-7',
    calendar: 'M4 5h16v16H4z M4 10h16 M8 3v4 M16 3v4',
    shop: 'M3 9l2-5h14l2 5v3H3z M5 12v9h14v-9 M9 21v-7h6v7',
    clipboard: 'M7 5H4v16h16V5h-3 M9 3h6v4H9z M8 12h8 M8 16h8',
    arrow: 'M5 12h14 M13 6l6 6l-6 6',
    info: 'M12 21a9 9 0 1 0 0-18a9 9 0 0 0 0 18 M12 11v6 M12 7v.01',
    filter: 'M3 5h18 M7 12h10 M10 19h4'
  };
}
