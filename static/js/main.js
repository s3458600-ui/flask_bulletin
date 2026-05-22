let authModal;

$(document).ready(function() {
    authModal = new bootstrap.Modal(document.getElementById('authModal'));
    
    // 초기 로드
    checkAuth();
    loadList();

    // 화면 이동 단순 라우팅 트리거
    $('#go-home, #detail-close, #form-cancel').click(() => showPage('list'));
    $('#go-write').click(() => openForm(null));
    $('#go-edit').click(function() { openForm($(this).data('id')); });

    // 테이블 행 클릭 시 내용 보기
    $(document).on('click', '.post-row', function() {
        loadDetail($(this).data('id'));
    });

    // 인증 팝업 제어 및 스위칭
    $(document).on('click', '#btn-show-login', () => authModal.show());
    $('#switch-join').click(() => { $('#auth-login-view').addClass('d-none'); $('#auth-join-view').removeClass('d-none'); });
    $('#switch-login').click(() => { $('#auth-join-view').addClass('d-none'); $('#auth-login-view').removeClass('d-none'); });

    // API 연동 액션들
    $('#action-login').click(loginSubmit);
    $('#action-join').click(joinSubmit);
    $(document).on('click', '#btn-action-logout', logoutSubmit);
    $('#action-save').click(savePostSubmit);
    $('#action-delete').click(function() { deletePostSubmit($(this).data('id')); });
});

// UI 페이지 전환 함수
function showPage(pageId) {
    $('#page-list, #page-detail, #page-form').addClass('d-none');
    $(`#page-${pageId}`).removeClass('d-none');
    if(pageId === 'list') loadList();
}

// 로그인 세션 여부 체크
function checkAuth() {
    $.get('/api/auth/status', function(res) {
        if(res.logged_in) {
            $('#nav-auth').html(`<span class="fw-bold me-2">${res.name}님</span><button class="btn btn-light btn-sm" id="btn-action-logout">로그아웃</button>`);
            $('#go-write').removeClass('d-none');
        } else {
            $('#nav-auth').html(`<button class="btn btn-primary btn-sm" id="btn-show-login">로그인</button>`);
            $('#go-write').addClass('d-none');
        }
    });
}

function loginSubmit() {
    const data = { username: $('#in-username').val(), password: $('#in-password').val() };
    $.ajax({
        url: '/api/auth/login', method: 'POST', contentType: 'application/json', data: JSON.stringify(data),
        success: () => { authModal.hide(); checkAuth(); loadList(); },
        error: (xhr) => alert(xhr.responseJSON.message)
    });
}

function joinSubmit() {
    const data = { username: $('#join-username').val(), password: $('#join-password').val(), name: $('#join-name').val() };
    $.ajax({
        url: '/api/auth/join', method: 'POST', contentType: 'application/json', data: JSON.stringify(data),
        success: () => { alert('가입되었습니다! 로그인해주세요.'); $('#switch-login').click(); },
        error: (xhr) => alert(xhr.responseJSON.message)
    });
}

function logoutSubmit() {
    $.post('/api/auth/logout', () => { checkAuth(); showPage('list'); });
}

// [READ] 리스트 출력
function loadList() {
    $.get('/api/posts', function(posts) {
        let rows = '';
        posts.forEach(p => {
            rows += `<tr class="post-row" data-id="${p.id}"><td>${p.id}</td><td class="fw-bold">${p.title}</td><td>${p.author}</td><td class="text-muted">${p.date}</td></tr>`;
        });
        $('#list-body').html(rows || '<tr><td colspan="4" class="text-center py-4 text-muted">등록된 글이 없습니다.</td></tr>');
    });
}

// [READ] 상세조회
function loadDetail(id) {
    $.get(`/api/posts/${id}`, function(res) {
        $('#view-title').text(res.post.title);
        $('#view-author').text(`작성자 : ${res.post.author}`);
        $('#view-content').text(res.post.content);
        $('#go-edit, #action-delete').data('id', res.post.id);
        
        if(res.is_owner) $('#owner-buttons').removeClass('d-none');
        else $('#owner-buttons').addClass('d-none');
        
        showPage('detail');
    });
}

// [CREATE / UPDATE Form 진입]
function openForm(id) {
    if(id) { // 수정 모드
        $.get(`/api/posts/${id}`, function(res) {
            $('#form-mode-title').text('글 수정하기');
            $('#form-id').val(res.post.id);
            $('#form-title-input').val(res.post.title);
            $('#form-content-input').val(res.post.content);
            showPage('form');
        });
    } else { // 신규 작성 모드
        $('#form-mode-title').text('새 글 작성');
        $('#form-id').val('');
        $('#form-title-input').val('');
        $('#form-content-input').val('');
        showPage('form');
    }
}

// [CREATE / UPDATE Submit]
function savePostSubmit() {
    const id = $('#form-id').val();
    const data = { title: $('#form-title-input').val(), content: $('#form-content-input').val() };
    const url = id ? `/api/posts/${id}` : '/api/posts';
    const method = id ? 'PUT' : 'POST';

    $.ajax({
        url: url, method: method, contentType: 'application/json', data: JSON.stringify(data),
        success: () => showPage('list')
    });
}

// [DELETE]
function deletePostSubmit(id) {
    if(confirm('정말 삭제하시겠습니까?')) {
        $.ajax({ url: `/api/posts/${id}`, method: 'DELETE', success: () => showPage('list') });
    }
}
