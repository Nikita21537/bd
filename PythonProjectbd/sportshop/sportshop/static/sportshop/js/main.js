const SportShop = {
    // Форматирование цены
    formatPrice(price) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0
        }).format(price);
    },

    // Форматирование даты
    formatDate(date) {
        return new Date(date).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },

    // Получение CSRF токена
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },

    // Отображение уведомления
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Удаление при клике
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });

        // Автоматическое скрытие
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    },

    // Проверка валидности email
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Проверка валидности телефона (российский формат)
    isValidPhone(phone) {
        const re = /^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$/;
        return re.test(phone.replace(/\s+/g, ''));
    },

    // Загрузка изображения с превью
    previewImage(input, previewId) {
        const preview = document.getElementById(previewId);
        const file = input.files[0];

        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    },

    // Подсчет символов в textarea
    countChars(textareaId, counterId, maxLength) {
        const textarea = document.getElementById(textareaId);
        const counter = document.getElementById(counterId);

        if (textarea && counter) {
            const updateCounter = () => {
                const length = textarea.value.length;
                counter.textContent = `${length}/${maxLength}`;

                if (length > maxLength) {
                    counter.style.color = '#DC2626';
                } else if (length > maxLength * 0.9) {
                    counter.style.color = '#D97706';
                } else {
                    counter.style.color = '#6B7280';
                }
            };

            textarea.addEventListener('input', updateCounter);
            updateCounter(); // Инициализация
        }
    }
};

// Корзина
class CartManager {
    constructor() {
        this.cartCountElement = document.getElementById('cart-count');
        this.initializeEventListeners();
        this.updateCartCount();
    }

    initializeEventListeners() {
        // Кнопки "В корзину" на страницах товаров
        document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = btn.dataset.productId;
                const quantity = btn.dataset.quantity || 1;
                this.addToCart(productId, quantity);
            });
        });

        // Обновление количества в корзине
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.parentElement.querySelector('.quantity-input');
                const productId = btn.closest('.cart-item').dataset.productId;
                const change = btn.classList.contains('decrease') ? -1 : 1;

                let newValue = parseInt(input.value) + change;
                if (newValue < 1) newValue = 1;
                if (newValue > 99) newValue = 99;

                input.value = newValue;
                this.updateCartItem(productId, newValue);
            });
        });

        // Удаление из корзины
        document.querySelectorAll('.remove-from-cart').forEach(btn => {
            btn.addEventListener('click', () => {
                const productId = btn.dataset.productId;
                if (confirm('Удалить товар из корзины?')) {
                    this.removeFromCart(productId);
                }
            });
        });
    }

    async addToCart(productId, quantity = 1) {
        try {
            const response = await fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SportShop.getCSRFToken()
                },
                body: JSON.stringify({ quantity: quantity })
            });

            const data = await response.json();

            if (data.success) {
                SportShop.showNotification(data.message || 'Товар добавлен в корзину');
                this.updateCartCount(data.cart_count);

                // Обновляем отображение на странице корзины
                if (window.location.pathname.includes('/cart/')) {
                    this.refreshCart();
                }
            } else {
                SportShop.showNotification(data.error || 'Ошибка при добавлении в корзину', 'error');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            SportShop.showNotification('Ошибка при добавлении в корзину', 'error');
        }
    }

    async updateCartItem(productId, quantity) {
        try {
            const response = await fetch(`/cart/update/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SportShop.getCSRFToken()
                },
                body: JSON.stringify({ quantity: quantity })
            });

            const data = await response.json();

            if (data.success) {
                this.updateCartCount(data.cart_count);

                // Обновляем отображение на странице корзины
                if (window.location.pathname.includes('/cart/')) {
                    this.updateCartDisplay(data);
                }
            }
        } catch (error) {
            console.error('Error updating cart:', error);
            SportShop.showNotification('Ошибка при обновлении корзины', 'error');
        }
    }

    async removeFromCart(productId) {
        try {
            const response = await fetch(`/cart/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': SportShop.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                SportShop.showNotification('Товар удален из корзины');
                this.updateCartCount(data.cart_count);

                // Обновляем отображение на странице корзины
                if (window.location.pathname.includes('/cart/')) {
                    document.querySelector(`.cart-item[data-product-id="${productId}"]`).remove();

                    // Обновляем итоги
                    this.updateCartTotals(data);

                    // Если корзина пуста, показываем сообщение
                    if (data.cart_count === 0) {
                        this.showEmptyCart();
                    }
                }
            }
        } catch (error) {
            console.error('Error removing from cart:', error);
            SportShop.showNotification('Ошибка при удалении из корзины', 'error');
        }
    }

    updateCartCount(count) {
        if (this.cartCountElement) {
            this.cartCountElement.textContent = count;
            this.cartCountElement.classList.add('updated');

            setTimeout(() => {
                this.cartCountElement.classList.remove('updated');
            }, 300);
        }
    }

    updateCartDisplay(data) {
        // Обновляем общую сумму
        const subtotalElement = document.getElementById('cart-subtotal');
        const grandTotalElement = document.getElementById('cart-grand-total');

        if (subtotalElement) {
            subtotalElement.textContent = SportShop.formatPrice(data.cart_subtotal);
        }

        if (grandTotalElement) {
            grandTotalElement.textContent = SportShop.formatPrice(data.cart_grand_total);
        }
    }

    updateCartTotals(data) {
        const elements = {
            'cart-subtotal': data.cart_subtotal,
            'cart-discount': data.cart_discount || 0,
            'cart-grand-total': data.cart_grand_total
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = SportShop.formatPrice(value);
            }
        }
    }

    showEmptyCart() {
        const cartContainer = document.querySelector('.cart-container');
        if (cartContainer) {
            cartContainer.innerHTML = `
                <div class="empty-cart">
                    <div class="empty-cart-icon">🛒</div>
                    <h2>Ваша корзина пуста</h2>
                    <p>Добавьте товары из каталога, чтобы сделать заказ</p>
                    <a href="/catalog/" class="btn btn-primary">Перейти в каталог</a>
                </div>
            `;
        }
    }

    refreshCart() {
        // Перезагружаем страницу корзины
        if (window.location.pathname.includes('/cart/')) {
            window.location.reload();
        }
    }
}

// Отзывы
class ReviewManager {
    constructor() {
        this.initializeRatingStars();
        this.initializeReviewForms();
    }

    initializeRatingStars() {
        document.querySelectorAll('.rating-stars').forEach(starsContainer => {
            const ratingInput = starsContainer.parentElement.querySelector('input[type="hidden"]');

            starsContainer.querySelectorAll('.star').forEach(star => {
                star.addEventListener('mouseover', (e) => {
                    const rating = e.target.dataset.rating;
                    this.highlightStars(starsContainer, rating);
                });

                star.addEventListener('click', (e) => {
                    const rating = e.target.dataset.rating;
                    ratingInput.value = rating;
                    this.setActiveStars(starsContainer, rating);
                });
            });

            starsContainer.addEventListener('mouseleave', () => {
                const currentRating = ratingInput.value || 0;
                this.setActiveStars(starsContainer, currentRating);
            });
        });
    }

    highlightStars(container, rating) {
        container.querySelectorAll('.star').forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#EA580C';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    setActiveStars(container, rating) {
        container.querySelectorAll('.star').forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#EA580C';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    initializeReviewForms() {
        document.querySelectorAll('.review-form').forEach(form => {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const productId = form.dataset.productId;
                const rating = form.querySelector('input[name="rating"]').value;
                const comment = form.querySelector('textarea[name="comment"]').value;

                if (!rating || !comment.trim()) {
                    SportShop.showNotification('Пожалуйста, заполните все поля', 'error');
                    return;
                }

                try {
                    const response = await fetch(`/api/review/${productId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': SportShop.getCSRFToken()
                        },
                        body: JSON.stringify({ rating, comment })
                    });

                    const data = await response.json();

                    if (data.success) {
                        SportShop.showNotification(data.message);
                        form.reset();

                        // Обновляем отображение рейтинга на странице
                        const avgRatingElement = document.getElementById('average-rating');
                        const reviewsCountElement = document.getElementById('reviews-count');

                        if (avgRatingElement) {
                            avgRatingElement.textContent = data.average_rating;
                        }

                        if (reviewsCountElement) {
                            reviewsCountElement.textContent = data.reviews_count;
                        }

                        // Обновляем список отзывов
                        this.addNewReview(data.review || { rating, comment });
                    } else {
                        SportShop.showNotification(data.error, 'error');
                    }
                } catch (error) {
                    console.error('Error submitting review:', error);
                    SportShop.showNotification('Ошибка при отправке отзыва', 'error');
                }
            });
        });
    }

    addNewReview(reviewData) {
        const reviewsList = document.querySelector('.reviews-list');
        if (!reviewsList) return;

        const reviewElement = document.createElement('div');
        reviewElement.className = 'review-item';
        reviewElement.innerHTML = `
            <div class="review-header">
                <span class="review-author">Вы</span>
                <span class="review-rating">${'★'.repeat(reviewData.rating)}${'☆'.repeat(5 - reviewData.rating)}</span>
            </div>
            <p>${reviewData.comment}</p>
            <small class="text-muted">Только что</small>
        `;

        reviewsList.prepend(reviewElement);
    }
}

// Поиск
class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');

        if (this.searchInput) {
            this.initializeSearch();
        }
    }

    initializeSearch() {
        let timeoutId;

        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(timeoutId);

            const query = e.target.value.trim();

            if (query.length < 2) {
                this.hideResults();
                return;
            }

            timeoutId = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });

        // Скрытие результатов при клике вне
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.searchResults?.contains(e.target)) {
                this.hideResults();
            }
        });

        // Обработка нажатия Enter
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = this.searchInput.value.trim();
                if (query) {
                    window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    async performSearch(query) {
        try {
            const response = await fetch(`/search/?q=${encodeURIComponent(query)}&format=json`);
            const data = await response.json();

            if (data.products && data.products.length > 0) {
                this.showResults(data.products, query);
            } else {
                this.showNoResults(query);
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    showResults(products, query) {
        if (!this.searchResults) {
            this.searchResults = document.createElement('div');
            this.searchResults.id = 'search-results';
            this.searchResults.className = 'search-results';
            this.searchInput.parentElement.appendChild(this.searchResults);
        }

        let html = `
            <div class="search-results-header">
                <strong>Результаты поиска "${query}"</strong>
                <a href="/search/?q=${encodeURIComponent(query)}" class="see-all">Все результаты →</a>
            </div>
            <div class="search-results-list">
        `;

        products.slice(0, 5).forEach(product => {
            html += `
                <a href="/product/${product.id}/" class="search-result-item">
                    <div class="search-result-image">
                        ${product.image ? 
                            `<img src="${product.image}" alt="${product.name}">` : 
                            '<div class="no-image">Фото</div>'
                        }
                    </div>
                    <div class="search-result-info">
                        <div class="search-result-title">${product.name}</div>
                        <div class="search-result-price">${SportShop.formatPrice(product.price)}</div>
                    </div>
                </a>
            `;
        });

        html += `</div>`;
        this.searchResults.innerHTML = html;
        this.searchResults.style.display = 'block';
    }

    showNoResults(query) {
        if (!this.searchResults) {
            this.searchResults = document.createElement('div');
            this.searchResults.id = 'search-results';
            this.searchResults.className = 'search-results';
            this.searchInput.parentElement.appendChild(this.searchResults);
        }

        this.searchResults.innerHTML = `
            <div class="search-no-results">
                <div class="search-no-results-icon">🔍</div>
                <div class="search-no-results-text">
                    <strong>По запросу "${query}" ничего не найдено</strong>
                    <small>Попробуйте изменить запрос</small>
                </div>
            </div>
        `;
        this.searchResults.style.display = 'block';
    }

    hideResults() {
        if (this.searchResults) {
            this.searchResults.style.display = 'none';
        }
    }
}

// Оформление заказа
class CheckoutManager {
    constructor() {
        this.initializeDeliveryOptions();
        this.initializePaymentMethods();
        this.initializeAddressSelection();
    }

    initializeDeliveryOptions() {
        document.querySelectorAll('input[name="delivery_method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateDeliveryInfo(e.target.value);
                this.updateOrderSummary();
            });
        });
    }

    initializePaymentMethods() {
        document.querySelectorAll('input[name="payment_method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updatePaymentInfo(e.target.value);
            });
        });
    }

    initializeAddressSelection() {
        document.querySelectorAll('input[name="address_id"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateAddressInfo(e.target.value);
            });
        });

        // Форма добавления нового адреса
        const addAddressBtn = document.getElementById('add-address-btn');
        const addressForm = document.getElementById('new-address-form');

        if (addAddressBtn && addressForm) {
            addAddressBtn.addEventListener('click', () => {
                addressForm.style.display = addressForm.style.display === 'none' ? 'block' : 'none';
            });
        }
    }

    updateDeliveryInfo(method) {
        const deliveryInfo = {
            pickup: {
                title: 'Самовывоз',
                description: 'Забрать из нашего магазина по адресу: ул. Спортивная, д. 10',
                eta: '1-2 дня',
                cost: 0
            },
            courier: {
                title: 'Курьерская доставка',
                description: 'Доставка курьером по Москве и области',
                eta: '1-3 дня',
                cost: 300
            },
            post: {
                title: 'Почта России',
                description: 'Доставка в отделение Почты России',
                eta: '5-14 дней',
                cost: 250
            },
            cdek: {
                title: 'СДЭК',
                description: 'Доставка в пункт выдачи СДЭК',
                eta: '3-7 дней',
                cost: 350
            }
        };

        const info = deliveryInfo[method] || deliveryInfo.courier;
        const element = document.getElementById('delivery-info');

        if (element) {
            element.innerHTML = `
                <h4>${info.title}</h4>
                <p>${info.description}</p>
                <p><strong>Срок доставки:</strong> ${info.eta}</p>
                <p><strong>Стоимость:</strong> ${info.cost === 0 ? 'Бесплатно' : SportShop.formatPrice(info.cost)}</p>
            `;
        }
    }

    updatePaymentInfo(method) {
        const paymentInfo = {
            card: 'Оплата банковской картой онлайн',
            cash: 'Оплата наличными при получении',
            invoice: 'Безналичный расчет для юридических лиц'
        };

        const element = document.getElementById('payment-info');
        if (element) {
            element.textContent = paymentInfo[method] || '';
        }
    }

    updateAddressInfo(addressId) {
        // В реальном приложении здесь был бы запрос к серверу
        console.log('Selected address:', addressId);
    }

    updateOrderSummary() {
        // Обновление итоговой суммы с учетом доставки
        const subtotal = parseFloat(document.getElementById('order-subtotal').dataset.value);
        const deliveryCost = this.getDeliveryCost();
        const total = subtotal + deliveryCost;

        document.getElementById('delivery-cost').textContent = SportShop.formatPrice(deliveryCost);
        document.getElementById('order-total').textContent = SportShop.formatPrice(total);
    }

    getDeliveryCost() {
        const selectedMethod = document.querySelector('input[name="delivery_method"]:checked');
        const costs = {
            pickup: 0,
            courier: 300,
            post: 250,
            cdek: 350
        };

        return costs[selectedMethod?.value] || 0;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация менеджеров
    const cartManager = new CartManager();
    const reviewManager = new ReviewManager();
    const searchManager = new SearchManager();
    const checkoutManager = new CheckoutManager();

    // Плавная прокрутка для якорей
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Подтверждение действий
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Вы уверены?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Табы
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.dataset.tab;

            // Скрываем все табы
            document.querySelectorAll('.tab-pane').forEach(tab => {
                tab.classList.remove('active');
            });

            // Деактивируем все кнопки
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });

            // Показываем выбранный таб
            document.getElementById(tabId).classList.add('active');
            this.classList.add('active');
        });
    });

    // Аккордеоны
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', function() {
            const accordion = this.parentElement;
            const content = this.nextElementSibling;

            accordion.classList.toggle('active');

            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    });

    // Ленивая загрузка изображений
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Обработка форм с валидацией
    document.querySelectorAll('.needs-validation').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }

            this.classList.add('was-validated');
        });
    });

    // Динамическое обновление количества товаров на складе
    document.querySelectorAll('.stock-indicator').forEach(indicator => {
        const stock = parseInt(indicator.dataset.stock);

        if (stock <= 0) {
            indicator.className = 'stock-indicator stock-out';
            indicator.textContent = 'Нет в наличии';
        } else if (stock < 10) {
            indicator.className = 'stock-indicator stock-low';
            indicator.textContent = `Осталось ${stock} шт.`;
        } else {
            indicator.className = 'stock-indicator stock-available';
            indicator.textContent = 'В наличии';
        }
    });

    // Обновление цены при изменении количества
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const pricePerUnit = parseFloat(this.dataset.price);
            const totalElement = this.closest('.quantity-selector').querySelector('.item-total');

            if (totalElement) {
                const total = pricePerUnit * parseInt(this.value);
                totalElement.textContent = SportShop.formatPrice(total);
            }
        });
    });

    // Инициализация кастомных селектов
    document.querySelectorAll('.custom-select').forEach(select => {
        const selected = select.querySelector('.select-selected');
        const options = select.querySelector('.select-options');

        selected.addEventListener('click', function() {
            select.classList.toggle('open');
        });

        options.querySelectorAll('.select-option').forEach(option => {
            option.addEventListener('click', function() {
                const value = this.dataset.value;
                const text = this.textContent;

                selected.querySelector('.select-value').textContent = text;
                select.querySelector('input[type="hidden"]').value = value;

                select.classList.remove('open');

                // Триггерим событие изменения
                const event = new Event('change');
                select.dispatchEvent(event);
            });
        });

        // Закрытие при клике вне
        document.addEventListener('click', function(e) {
            if (!select.contains(e.target)) {
                select.classList.remove('open');
            }
        });
    });

    console.log('SportShop initialized successfully!');
});
