import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/pages/HomeView.vue';
import AboutView from '@/pages/AboutView.vue';
import PostCreateView from '@/pages/posts/PostCreateView.vue';
import PostDetailView from '@/pages/posts/PostDetailView.vue';
import PostListView from '@/pages/posts/PostListView.vue';
import PostEditView from '@/pages/posts/PostEditView.vue';
import NotFoundView from '@/pages/NotFoundView.vue';
import NestedView from '@/pages/nested/NestedView.vue';
import NestedOneView from '@/pages/nested/NestedOneView.vue';
import NestedTwoView from '@/pages/nested/NestedTwoView.vue';
import NestedHomeView from '@/pages/nested/NestedHomeView.vue';
import MyPage from '@/pages/MyPage.vue';

const routes = [
	{
		path: '/',
		name: 'Home',
		component: HomeView,
	},
	{
		path: '/about',
		name: 'About',
		component: AboutView,
	},
	{
		path: '/posts',
		name: 'PostList',
		component: PostListView,
	},
	{
		path: '/posts/create',
		name: 'PostCreate',
		component: PostCreateView,
	},
	{
		path: '/posts/:id',
		name: 'PostDetail',
		component: PostDetailView,
		props: true,
		// props: route => ({ id: parseInt(route.params.id) }),
	},
	{
		path: '/posts/:id/edit',
		name: 'PostEdit',
		component: PostEditView,
	},
	{
		path: '/:pathMatch(.*)*',
		name: 'NotFound',
		component: NotFoundView,
	},
	{
		path: '/nested',
		name: 'Nested',
		component: NestedView,
		children: [
			{
				path: '',
				name: 'NestedHome',
				component: NestedHomeView,
			},
			{
				path: 'one',
				name: 'NestedOne',
				component: NestedOneView,
			},
			{
				path: 'two',
				name: 'NestedTwo',
				component: NestedTwoView,
			},
		],
	},
	{
		path: '/my',
		name: 'MyPage',
		component: MyPage,
		beforeEnter: [removeQueryString],
	},
];
function removeQueryString(to) {
	if (Object.keys(to.query).length > 0) {
		return { path: to.path, query: {} };
	}
}
const router = createRouter({
	history: createWebHistory(),
	// history: createWebHashHistory(),
	routes,
});

router.beforeEach((to, from) => {
	console.log('to: ', to);
	console.log('from: ', from);
	if (to.name === 'MyPage') {
		// router.push({name: 'Home'})
		// return false;
		// return { name: 'Home' };
		return '/posts';
	}
});

export default router;
