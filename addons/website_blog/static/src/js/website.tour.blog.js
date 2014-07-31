(function () {
    'use strict';

    var _t = openerp._t;

    openerp.Tour.register({
        id:   'blog',
        name: _t("Create a blog post"),
        steps: [
            {
                title:     _t("New Blog Post"),
                content:   _t("Let's go through the first steps to write beautiful blog posts."),
                popover:   { next: _t("Start Tutorial"), end: _t("Skip") },
            },
            {
                element:   '#content-menu-button',
                placement: 'left',
                title:     _t("Add Content"),
                content:   _t("Use this <em>'Content'</em> menu to create a new blog post like any other document (page, menu, products, event, ...)."),
                popover:   { fixed: true },
            },
            {
                element:   'a[data-action=new_blog_post]',
                placement: 'left',
                title:     _t("New Blog Post"),
                content:   _t("Select this menu item to create a new blog post."),
                popover:   { fixed: true },
            },
            {
                waitFor:   'body:has(button[data-action=save]:visible):has(.js_blog)',
                title:     _t("Blog Post Created"),
                content:   _t("This is your new blog post. Let's edit it."),
                popover:   { next: _t("Continue") },
            },
            {
                element:   'h1[data-oe-expression="blog_post.name"]',
                placement: 'top',
                title:     _t("Set a Title"),
                content:   _t("Click on this area and set a catchy title for your blog post."),
            },    
            {
                waitNot:   'h1#blog_post_name:empty()',
                element:   'h1[data-oe-expression="blog_post.name"]',
                placement: 'top',
                title:     _t("Change Title, subtitle"),
                content:   _t("Write a title, the subtitle is optional."),
                popover:   { next: _t("Continue") },
                
            },                    
            {
                element:   '.oe_cover_menu',
                placement: 'bottom',
                title:     _t("Customize Cover"),
                content:   _t("Change and customize your blog post cover"),
                popover:   { fixed: true },
            },
            {
                element:   '#change_cover',
                placement: 'left',
                title:     _t("Change Cover"),
                content:   _t("Select this menu item to chnage blog cover."),
                popover:   { fixed: true },
            }, 
            {
                element:   '.modal:has(.modal-dialog.select-media) button[data-dismiss=modal]',
                placement: 'right',
                title:     _t("Select Cover"),
                content:   _t("Select the appropriate cover and click on save."),
                popover:   { next: _t("Continue") },
            },
            {
                waitNot:   '.modal:has(.modal-dialog.select-media) button[data-dismiss=modal]',
                element:   '#blog_content',
                placement: 'top',
                title:     _t("Content"),
                content:   _t("Start writing your story here. Click on save in the upper left corner when you are done."),
            },            
            {
                
                waitNot:   '#blog_content .container.readable:empty()',
                element:   'button[data-action=snippet]',
                placement: 'right',
                title:     _t("Layout Your Blog Post"),
                content:   _t("Use well designed building blocks to structure the content of your blog. Click 'Insert Blocks' to add new content."),
                popover:   { fixed: true },
            },
            {
                snippet:   '#snippet_structure .oe_snippet:eq(2)',
                placement: 'bottom',
                title:     _t("Drag & Drop a Block"),
                content:   _t("Drag this block and drop it in your page."),
                popover:   { fixed: true },
            },
            {
                element:   'button[data-action=snippet]',
                placement: 'bottom',
                title:     _t("Add Another Block"),
                content:   _t("Let's add another block to your post."),
                popover:   { fixed: true },
            },
            {
                snippet:   '#snippet_structure .oe_snippet:eq(4)',
                placement: 'bottom',
                title:     _t("Drag & Drop a block"),
                content:   _t("Drag this block and drop it below the image block."),
                popover:   { fixed: true },
            },
            {
                element:   '.oe_active .oe_snippet_remove',
                placement: 'top',
                title:     _t("Delete the block"),
                content:   _t("From this toolbar you can move, duplicate or delete the selected zone. Click on the garbage can image to delete the block. Or click on the Title and delete it."),
            },
            {
                waitNot:   '.oe_active .oe_snippet_remove:visible',
                element:   'button[data-action=save]',
                placement: 'right',
                title:     _t("Save Your Blog"),
                content:   _t("Click the <em>Save</em> button to record changes on the page."),
                popover:   { fixed: true },
            },
            {
                waitNot:   'button[data-action=edit]:visible',
                element:   'a[data-action=show-mobile-preview]',
                placement: 'bottom',
                title:     _t("Mobile Preview"),
                content:   _t("Click on the mobile icon to preview how your blog post will be displayed on a mobile device."),
                popover:   { fixed: true },
            },  
            {
                element:   '.modal:has(#mobile-viewport) button[data-dismiss=modal]',
                placement: 'right',
                title:     _t("Check Mobile Preview"),
                content:   _t("Scroll to check rendering and then close the mobile preview."),
                popover:   { next: _t("Continue") },
            },

            {
                waitNot:   '.modal:has(#mobile-viewport) button[data-dismiss=modal]',
                element:   'a[data-action=promote-current-page]',
                placement: 'bottom',
                title:     _t("Promote this page"),
                content:   _t("Get this page efficiently referenced in Google to attract more visitors."),
                popover:   { fixed: true },
                
            }, 
            {
                element:   '.modal.oe_seo_configuration',
                placement: 'right',
                title:     _t("Promote information"),
                content:   _t("Fill the appropriate information and click on save"),
                popover:   { next: _t("Continue") },
            },
                               
            {
                waitFor:   '.modal.oe_seo_configuration[aria-hidden="true"]',
                element:   'button.btn-danger.js_publish_btn',
                placement: 'top',
                title:     _t("Publishing status"),
                content:   _t(" Click on this button to send your blog post online."),
            },
            {
                waitFor:   '.js_publish_management button.js_publish_btn.btn-success:visible',
                title:     "Thanks!",
                content:   _t("This tutorial is finished. To discover more features, improve the content of this page and try the <em>Promote</em> button in the top right menu."),
                popover:   { next: _t("Close Tutorial") },
            },
        ]
    });

}());
