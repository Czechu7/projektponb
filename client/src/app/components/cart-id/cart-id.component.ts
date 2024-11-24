import { Component, inject } from '@angular/core';
import { AccountService } from '../../_services/account.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-cart-id',
  standalone: true,
  imports: [],
  templateUrl: './cart-id.component.html',
  styleUrl: './cart-id.component.css'
})
export class CartIdComponent {
  accountService = inject(AccountService)
  route = inject(ActivatedRoute);
  
  cart: any;
  id: number = 0;
  ngOnInit() {
    this.id = this.route.snapshot.params['id'];
    this.accountService.getCartById(this.id).subscribe({
      next: cart => this.cart = cart,
      error: error => console.log(error),
      complete: () => console.log('Request has been completed')
    });
  }


}
