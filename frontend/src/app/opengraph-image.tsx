import { ImageResponse } from 'next/og'


export const alt = 'PrismPro — Make the work behind your resume visible'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: '#ece9e3',
          color: '#171717',
          padding: '68px 76px',
          fontFamily: 'Arial, sans-serif',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '2px solid rgba(23, 23, 23, 0.18)',
            paddingBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', fontSize: 34, fontWeight: 700 }}>
            PRISMPRO
          </div>
          <div
            style={{
              display: 'flex',
              fontSize: 18,
              fontWeight: 700,
              letterSpacing: '0.16em',
            }}
          >
            PRIVATE PREVIEW · IN DEVELOPMENT
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          <div
            style={{
              display: 'flex',
              maxWidth: '1000px',
              fontSize: 82,
              fontWeight: 700,
              letterSpacing: '-0.055em',
              lineHeight: 0.96,
            }}
          >
            Make the work behind your resume visible.
          </div>
          <div
            style={{
              display: 'flex',
              maxWidth: '900px',
              fontSize: 28,
              lineHeight: 1.35,
              color: 'rgba(23, 23, 23, 0.72)',
            }}
          >
            {'A career-evidence coach that interviews before it writes and uses only candidate-confirmed facts.'}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: '0.12em',
          }}
        >
          <div style={{ display: 'flex' }}>CAREER SUPPORT WITHOUT CAREER FICTION.</div>
          <div style={{ display: 'flex' }}>PRISMPRO.LIVE</div>
        </div>
      </div>
    ),
    size,
  )
}
