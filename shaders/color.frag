//varying vec2 out_uv;
uniform sampler2D videoSampler;

void main()
{
        //gl_FragColor = texture2D (videoSampler, out_uv);
        gl_FragColor = vec4(1,0,1,1);
}